#!/usr/bin/env python3
"""Ingest lodging (hotels) for Manhattan from Google Places API (New) into Firestore."""
import json
import math
import subprocess
import time
import urllib.request

# ── Config ──
PLACES_API_KEY = "AIzaSyDVuhME-g_3QakgS4cmtWlYR01uns2kG1A"
PROJECT = "oasis-bde20"
GCLOUD_TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
FS_HEADERS = {"Authorization": f"Bearer {GCLOUD_TOKEN}", "Content-Type": "application/json"}
FS_BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

BBOX = {"lat_min": 40.680, "lat_max": 40.882, "lng_min": -74.047, "lng_max": -73.907}
RADIUS_M = 2000  # 2km radius per search
CHUNK_SIZE = 800

api_requests = 0


# ── Google Places API (New) ──
def nearby_search(lat, lng, radius, page_token=None):
    """Search for lodging using Places API (New) Nearby Search."""
    global api_requests
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,"
                            "places.currentOpeningHours,places.regularOpeningHours,"
                            "places.accessibilityOptions,places.formattedAddress",
    }
    body = {
        "includedTypes": ["lodging"],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius,
            }
        },
        "maxResultCount": 20,
        "languageCode": "en",
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    api_requests += 1
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"    API error {e.code}: {err[:200]}")
        return {"places": []}


# ── Grid generation ──
def generate_grid(bbox, radius_m):
    """Generate grid of circle centers to cover the bbox."""
    # Approx degrees per meter at this latitude
    lat_mid = (bbox["lat_min"] + bbox["lat_max"]) / 2
    deg_per_m_lat = 1 / 111320
    deg_per_m_lng = 1 / (111320 * math.cos(math.radians(lat_mid)))

    # Step = radius * sqrt(2) for overlap coverage (diamond pattern)
    step_lat = radius_m * 1.5 * deg_per_m_lat
    step_lng = radius_m * 1.5 * deg_per_m_lng

    centers = []
    lat = bbox["lat_min"]
    row = 0
    while lat <= bbox["lat_max"]:
        lng_start = bbox["lng_min"] + (step_lng / 2 if row % 2 else 0)
        lng = lng_start
        while lng <= bbox["lng_max"]:
            centers.append((lat, lng))
            lng += step_lng
        lat += step_lat
        row += 1
    return centers


# ── Firestore helpers ──
def fs_get(path):
    req = urllib.request.Request(f"{FS_BASE}/{path}", headers=FS_HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fs_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{FS_BASE}/{path}", data=data, headers=FS_HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fs_delete(path):
    req = urllib.request.Request(f"{FS_BASE}/{path}", headers=FS_HEADERS, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def pv(v):
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return float(v["doubleValue"])
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "arrayValue" in v: return [pv(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v: return {k: pv(fv) for k, fv in v["mapValue"].get("fields", {}).items()}
    return str(v)


def to_fv(val):
    if val is None: return {"nullValue": None}
    if isinstance(val, bool): return {"booleanValue": val}
    if isinstance(val, int): return {"integerValue": str(val)}
    if isinstance(val, float): return {"doubleValue": val}
    if isinstance(val, str): return {"stringValue": val}
    if isinstance(val, list):
        if not val: return {"arrayValue": {}}
        return {"arrayValue": {"values": [to_fv(x) for x in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {k: to_fv(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def place_to_toilet(place):
    """Convert Places API (New) result to toilet object."""
    loc = place.get("location", {})
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    name = place.get("displayName", {}).get("text", "Hotel")
    types = place.get("types", [])

    # Extract hours
    hours = None
    reg_hours = place.get("regularOpeningHours", {})
    if reg_hours:
        descs = reg_hours.get("weekdayDescriptions", [])
        if descs:
            hours = descs  # list of strings

    return {
        "id": place.get("id", ""),
        "name": name,
        "lat": lat,
        "lng": lng,
        "cat": "Store",
        "tier": 3,
        "free": False,
        "isPartner": False,
        "isUnconfirmed": True,
        "hours": hours,
        "types": types,
        "source": "google",
    }


def is_in_bbox(t):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None: return False
    return BBOX["lat_min"] <= lat <= BBOX["lat_max"] and BBOX["lng_min"] <= lng <= BBOX["lng_max"]


def main():
    global api_requests

    # ── Step 1: Generate search grid ──
    centers = generate_grid(BBOX, RADIUS_M)
    print(f"Search grid: {len(centers)} circles (radius {RADIUS_M}m)\n")

    # ── Step 2: Search Google Places API ──
    print("Searching for lodging...")
    all_places = {}  # id -> place, for dedup
    for i, (lat, lng) in enumerate(centers):
        result = nearby_search(lat, lng, RADIUS_M)
        places = result.get("places", [])
        new = 0
        for p in places:
            pid = p.get("id")
            if pid and pid not in all_places:
                all_places[pid] = p
                new += 1
        print(f"  [{i+1}/{len(centers)}] ({lat:.3f}, {lng:.3f}): {len(places)} results, {new} new (total: {len(all_places)})")
        time.sleep(0.15)  # Rate limiting

    print(f"\nTotal unique lodging places found: {len(all_places)}")
    print(f"API requests used: {api_requests}")

    # ── Step 3: Convert and filter ──
    new_toilets = []
    for place in all_places.values():
        t = place_to_toilet(place)
        if is_in_bbox(t):
            new_toilets.append(t)

    print(f"In bbox: {len(new_toilets)} (filtered {len(all_places) - len(new_toilets)} outside)")

    # ── Step 4: Load existing data ──
    print("\nLoading existing Manhattan data...")
    existing = []
    existing_ids = set()
    old_chunk_count = 0
    for i in range(20):
        try:
            raw = fs_get(f"cities/manhattan/chunks/{i}")
            vals = raw.get("fields", {}).get("toilets", {}).get("arrayValue", {}).get("values", [])
            for item in vals:
                if "mapValue" in item:
                    t = {k: pv(fv) for k, fv in item["mapValue"]["fields"].items()}
                else:
                    t = pv(item)
                existing.append(t)
                existing_ids.add(t.get("id"))
            old_chunk_count = i + 1
        except urllib.error.HTTPError as e:
            if e.code == 404: break
            raise

    print(f"  Existing: {len(existing)} items in {old_chunk_count} chunks")

    # ── Step 5: Deduplicate ──
    dupes = sum(1 for t in new_toilets if t["id"] in existing_ids)
    unique_new = [t for t in new_toilets if t["id"] not in existing_ids]
    print(f"  Duplicates: {dupes}")
    print(f"  New unique: {len(unique_new)}")

    if not unique_new:
        print("\nNo new lodging to add.")
        return

    # ── Step 6: Merge and write ──
    merged = existing + unique_new
    print(f"\n  Merged total: {len(merged)}")

    new_chunks = [merged[i:i + CHUNK_SIZE] for i in range(0, len(merged), CHUNK_SIZE)]
    print(f"  Chunks: {len(new_chunks)}")

    print("\nWriting to Firestore...")
    for i, chunk in enumerate(new_chunks):
        print(f"  chunk {i} ({len(chunk)} items)...", end=" ", flush=True)
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        fs_patch(f"cities/manhattan/chunks/{i}", body)
        print("OK")

    # Delete extra old chunks
    for i in range(len(new_chunks), old_chunk_count):
        print(f"  Deleting old chunk {i}...")
        fs_delete(f"cities/manhattan/chunks/{i}")

    # Update metadata
    meta = {
        "fields": {
            "count": {"integerValue": str(len(merged))},
            "chunks": {"integerValue": str(len(new_chunks))},
            "lastUpdated": {"integerValue": str(int(time.time() * 1000))}
        }
    }
    fs_patch("cities/manhattan", meta)
    print("  Metadata updated.")

    # ── Report ──
    t3 = [t for t in merged if t.get("tier") == 3]
    tier_dist = {}
    for t in merged:
        tier_dist[t.get("tier", "?")] = tier_dist.get(t.get("tier", "?"), 0) + 1

    print(f"\n{'='*60}")
    print("INGEST REPORT")
    print(f"{'='*60}")
    print(f"  追加件数:            {len(unique_new)}")
    print(f"  修正後総件数:        {len(merged)}")
    print(f"  T3に分類された件数:  {len(t3)}")
    print(f"  APIリクエスト数:     {api_requests}")
    print(f"\n  Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(merged) * 100
        print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")
    print(f"\n  T3 例:")
    for t in t3[:3]:
        print(f"    {t['name']} ({t['lat']}, {t['lng']})")


if __name__ == "__main__":
    main()
