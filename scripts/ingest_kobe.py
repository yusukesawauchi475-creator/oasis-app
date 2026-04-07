#!/usr/bin/env python3
"""Ingest full Kobe data: public toilets, convenience stores, transit stations."""
import json
import math
import re
import subprocess
import time
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
FS_BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
PLACES_API_KEY = "AIzaSyDVuhME-g_3QakgS4cmtWlYR01uns2kG1A"
CHUNK_SIZE = 800

BBOX = {"lat_min": 34.610, "lat_max": 34.760, "lng_min": 135.070, "lng_max": 135.310}

JP_KONBINI = re.compile(
    r'(7[\-\s]?eleven|セブン[\-\s]?イレブン|familymart|ファミリーマート|'
    r'lawson|ローソン|ミニストップ|ministop|セイコーマート|seicomart)',
    re.IGNORECASE
)
LODGING_NAME = re.compile(r'\b(hotel|motel|hostel|inn|ホテル|旅館|民宿)\b', re.IGNORECASE)


# ── Firestore ──
def fs_get(path):
    req = urllib.request.Request(f"{FS_BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fs_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{FS_BASE}/{path}", data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fs_delete(path):
    req = urllib.request.Request(f"{FS_BASE}/{path}", headers=HEADERS, method="DELETE")
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


# ── Google Places API (New) ──
api_requests = 0

def nearby_search(lat, lng, radius, included_types):
    global api_requests
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,"
                            "places.regularOpeningHours,places.accessibilityOptions",
    }
    body = {
        "includedTypes": included_types,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius,
            }
        },
        "maxResultCount": 20,
        "languageCode": "ja",
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    api_requests += 1
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:200]
        print(f"      API error {e.code}: {err}")
        return {"places": []}


def generate_grid(bbox, radius_m):
    lat_mid = (bbox["lat_min"] + bbox["lat_max"]) / 2
    deg_lat = 1 / 111320
    deg_lng = 1 / (111320 * math.cos(math.radians(lat_mid)))
    step_lat = radius_m * 1.5 * deg_lat
    step_lng = radius_m * 1.5 * deg_lng
    centers = []
    lat = bbox["lat_min"]
    row = 0
    while lat <= bbox["lat_max"]:
        lng = bbox["lng_min"] + (step_lng / 2 if row % 2 else 0)
        while lng <= bbox["lng_max"]:
            centers.append((lat, lng))
            lng += step_lng
        lat += step_lat
        row += 1
    return centers


def in_bbox(lat, lng):
    if lat is None or lng is None: return False
    return BBOX["lat_min"] <= lat <= BBOX["lat_max"] and BBOX["lng_min"] <= lng <= BBOX["lng_max"]


def place_to_toilet(place, cat, tier):
    loc = place.get("location", {})
    lat, lng = loc.get("latitude"), loc.get("longitude")
    name = place.get("displayName", {}).get("text", "")
    types = place.get("types", [])
    hours = None
    reg = place.get("regularOpeningHours", {})
    if reg:
        descs = reg.get("weekdayDescriptions", [])
        if descs: hours = descs
    wheelchair = False
    acc = place.get("accessibilityOptions", {})
    if acc:
        wheelchair = acc.get("wheelchairAccessibleEntrance", False) or acc.get("wheelchairAccessibleRestroom", False)
    return {
        "id": place.get("id", ""),
        "name": name,
        "lat": lat,
        "lng": lng,
        "cat": cat,
        "tier": tier,
        "free": cat == "Public",
        "isPartner": False,
        "isUnconfirmed": False,
        "wheelchair": wheelchair,
        "hours": hours,
        "types": types,
        "source": "google",
    }


def search_category(label, included_types, cat, tier, radius=2000):
    """Search an entire category across the grid."""
    centers = generate_grid(BBOX, radius)
    all_places = {}
    print(f"  [{label}] grid={len(centers)} circles, radius={radius}m")
    for i, (lat, lng) in enumerate(centers):
        result = nearby_search(lat, lng, radius, included_types)
        places = result.get("places", [])
        new = 0
        for p in places:
            pid = p.get("id")
            if pid and pid not in all_places:
                loc = p.get("location", {})
                if in_bbox(loc.get("latitude"), loc.get("longitude")):
                    all_places[pid] = p
                    new += 1
        if (i + 1) % 10 == 0 or i == len(centers) - 1:
            print(f"    [{i+1}/{len(centers)}] total unique: {len(all_places)}")
        time.sleep(0.12)

    toilets = []
    for p in all_places.values():
        t = place_to_toilet(p, cat, tier)
        # Re-classify konbini
        if cat == "Store" and JP_KONBINI.search(t["name"]):
            t["cat"] = "Store"
            t["tier"] = 2
        toilets.append(t)
    return toilets


def main():
    global api_requests

    print("="*60)
    print("  KOBE FULL INGEST")
    print("="*60)

    # Load existing data (lodging)
    print("\nLoading existing Kobe data...")
    existing = []
    existing_ids = set()
    old_chunks = 0
    for i in range(10):
        try:
            raw = fs_get(f"cities/kobe/chunks/{i}")
            vals = raw["fields"]["toilets"]["arrayValue"]["values"]
            for item in vals:
                if "mapValue" in item:
                    t = {k: pv(fv) for k, fv in item["mapValue"]["fields"].items()}
                else:
                    t = pv(item)
                existing.append(t)
                existing_ids.add(t.get("id"))
            old_chunks = i + 1
        except urllib.error.HTTPError:
            break
    print(f"  Existing: {len(existing)} items (lodging)")

    all_new = []

    # 1. Public toilets
    print("\n--- Public Toilets ---")
    toilets_public = search_category(
        "public_bathroom", ["public_bathroom"], "Public", 1, radius=2500
    )
    print(f"  Found: {len(toilets_public)}")
    all_new.extend(toilets_public)

    # 2. Convenience stores
    print("\n--- Convenience Stores ---")
    toilets_conbini = search_category(
        "convenience_store", ["convenience_store"], "Store", 2, radius=1500
    )
    # All konbini → T2, others stay T4
    for t in toilets_conbini:
        if JP_KONBINI.search(t["name"]):
            t["tier"] = 2
        else:
            t["tier"] = 4
    print(f"  Found: {len(toilets_conbini)}")
    konbini_t2 = sum(1 for t in toilets_conbini if t["tier"] == 2)
    print(f"    Konbini (T2): {konbini_t2}, Other (T4): {len(toilets_conbini) - konbini_t2}")
    all_new.extend(toilets_conbini)

    # 3. Transit stations
    print("\n--- Transit Stations ---")
    toilets_transit = search_category(
        "transit_station", ["transit_station"], "Transit", 2, radius=2500
    )
    print(f"  Found: {len(toilets_transit)}")
    all_new.extend(toilets_transit)

    # 4. Train stations (separate type)
    print("\n--- Train Stations ---")
    toilets_train = search_category(
        "train_station", ["train_station"], "Transit", 2, radius=2500
    )
    # Dedup against transit
    transit_ids = {t["id"] for t in toilets_transit}
    toilets_train_new = [t for t in toilets_train if t["id"] not in transit_ids]
    print(f"  Found: {len(toilets_train)}, new (after dedup): {len(toilets_train_new)}")
    all_new.extend(toilets_train_new)

    # 5. Subway stations
    print("\n--- Subway Stations ---")
    toilets_subway = search_category(
        "subway_station", ["subway_station"], "Transit", 2, radius=2500
    )
    existing_transit_ids = {t["id"] for t in toilets_transit} | {t["id"] for t in toilets_train}
    toilets_subway_new = [t for t in toilets_subway if t["id"] not in existing_transit_ids]
    print(f"  Found: {len(toilets_subway)}, new (after dedup): {len(toilets_subway_new)}")
    all_new.extend(toilets_subway_new)

    # Dedup all_new against existing
    dedup_new = []
    seen = set(existing_ids)
    for t in all_new:
        if t["id"] not in seen:
            seen.add(t["id"])
            dedup_new.append(t)
    print(f"\n  Total new (deduped): {len(dedup_new)}")

    # Merge
    merged = existing + dedup_new
    print(f"  Merged total: {len(merged)}")

    # Write
    print("\nWriting to Firestore...")
    new_chunks = [merged[i:i+CHUNK_SIZE] for i in range(0, len(merged), CHUNK_SIZE)]
    for i, chunk in enumerate(new_chunks):
        print(f"  chunk {i} ({len(chunk)})...", end=" ", flush=True)
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        fs_patch(f"cities/kobe/chunks/{i}", body)
        print("OK")
    for i in range(len(new_chunks), old_chunks):
        try:
            fs_delete(f"cities/kobe/chunks/{i}")
        except Exception:
            pass
    fs_patch("cities/kobe", {"fields": {
        "count": {"integerValue": str(len(merged))},
        "chunks": {"integerValue": str(len(new_chunks))},
        "lastUpdated": {"integerValue": str(int(time.time() * 1000))},
    }})

    # Report
    tier_dist = {}
    cat_dist = {}
    for t in merged:
        tier_dist[t.get("tier", "?")] = tier_dist.get(t.get("tier", "?"), 0) + 1
        cat_dist[t.get("cat", "?")] = cat_dist.get(t.get("cat", "?"), 0) + 1

    print(f"\n{'='*60}")
    print("KOBE INGEST REPORT")
    print(f"{'='*60}")
    print(f"  総件数:          {len(merged)}")
    print(f"  API requests:    {api_requests}")
    print(f"\n  Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(merged) * 100
        print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")
    print(f"\n  Cat内訳:")
    for cat in sorted(cat_dist):
        print(f"    {cat}: {cat_dist[cat]}")

    # Samples per tier
    for tier in sorted(tier_dist):
        samples = [t for t in merged if t.get("tier") == tier][:3]
        print(f"\n  T{tier} 例:")
        for t in samples:
            print(f"    {t['name']} ({t.get('cat')}, {t.get('lat'):.4f}, {t.get('lng'):.4f})")


if __name__ == "__main__":
    main()
