#!/usr/bin/env python3
"""Apply Manhattan-equivalent fixes to all 7 remaining cities."""
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

CITIES = {
    "tokyo":     {"lat_min": 35.530, "lat_max": 35.820, "lng_min": 139.580, "lng_max": 139.920, "region": "jp"},
    "osaka":     {"lat_min": 34.590, "lat_max": 34.780, "lng_min": 135.380, "lng_max": 135.620, "region": "jp"},
    "kobe":      {"lat_min": 34.610, "lat_max": 34.760, "lng_min": 135.070, "lng_max": 135.310, "region": "jp"},
    "london":    {"lat_min": 51.340, "lat_max": 51.670, "lng_min": -0.250,  "lng_max": 0.010,   "region": "uk"},
    "sydney":    {"lat_min": -34.000,"lat_max": -33.730,"lng_min": 151.100, "lng_max": 151.320, "region": "au"},
    "melbourne": {"lat_min": -37.920,"lat_max": -37.700,"lng_min": 144.840, "lng_max": 145.080, "region": "au"},
    "brisbane":  {"lat_min": -27.580,"lat_max": -27.360,"lng_min": 152.930, "lng_max": 153.130, "region": "au"},
}

# Japan convenience stores → T2
JP_KONBINI = re.compile(
    r'(7[\-\s]?eleven|セブン[\-\s]?イレブン|familymart|ファミリーマート|'
    r'lawson|ローソン|ミニストップ|ministop|セイコーマート|seicomart)',
    re.IGNORECASE
)

# US/AU/UK chains → T3
CHAIN_T3 = re.compile(
    r'\b(cvs|walgreens?|duane\s*reade|rite\s*aid|target|whole\s*foods|trader\s*joe\'?s|'
    r'woolworths|coles|chemist\s*warehouse|7[\-\s]?eleven|starbucks)\b',
    re.IGNORECASE
)

# Lodging name patterns
LODGING_NAME = re.compile(
    r'\b(hilton|marriott|hyatt|sheraton|westin|ritz|four\s*seasons|w\s+hotel|kimpton|'
    r'intercontinental|holiday\s*inn|best\s*western|inn|suites|lodge|resort|hotel|motel|'
    r'hostel|ホテル|旅館|民宿)\b',
    re.IGNORECASE
)


# ── Firestore helpers ──
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


# ── Google Places API ──
def nearby_search(lat, lng, radius):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,"
                            "places.regularOpeningHours,places.formattedAddress",
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
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"      API error {e.code}: {e.read().decode()[:150]}")
        return {"places": []}


def generate_grid(bbox, radius_m):
    lat_mid = (bbox["lat_min"] + bbox["lat_max"]) / 2
    deg_per_m_lat = 1 / 111320
    deg_per_m_lng = 1 / (111320 * math.cos(math.radians(lat_mid)))
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


def place_to_toilet(place, bbox):
    loc = place.get("location", {})
    lat, lng = loc.get("latitude"), loc.get("longitude")
    name = place.get("displayName", {}).get("text", "Hotel")
    types = place.get("types", [])
    hours = None
    reg = place.get("regularOpeningHours", {})
    if reg:
        descs = reg.get("weekdayDescriptions", [])
        if descs:
            hours = descs
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


# ── Tier classification ──
def is_lodging(t):
    types = t.get("types")
    if isinstance(types, list):
        for tp in types:
            if isinstance(tp, str) and tp.lower() in ("lodging", "hotel"):
                return True
    name = t.get("name") or ""
    return bool(LODGING_NAME.search(name))


def classify_tier(t, region):
    if t.get("isPartner"):
        return 1
    cat = (t.get("cat") or "").strip()
    name = t.get("name") or ""

    # T1: Public
    if cat == "Public":
        return 1

    # T2: Transit / Station
    if cat in ("Transit", "Station"):
        return 2

    # Japan: konbini → T2
    if region == "jp" and cat == "Store" and JP_KONBINI.search(name):
        return 2

    # T3: Lodging
    if is_lodging(t):
        return 3

    # T3: Known chains (non-JP 7-Eleven handled here too)
    if cat == "Store":
        if region == "jp":
            # JP: no chain promotion to T3 (konbini already T2)
            pass
        else:
            if CHAIN_T3.search(name):
                return 3

    # T4: everything else
    return 4


def in_bbox(t, bbox):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None:
        return False
    return bbox["lat_min"] <= lat <= bbox["lat_max"] and bbox["lng_min"] <= lng <= bbox["lng_max"]


# ── Fetch existing data ──
def fetch_city(city_key):
    toilets = []
    chunk_count = 0
    for i in range(30):
        try:
            raw = fs_get(f"cities/{city_key}/chunks/{i}")
            vals = raw["fields"]["toilets"]["arrayValue"]["values"]
            for item in vals:
                if "mapValue" in item:
                    toilets.append({k: pv(fv) for k, fv in item["mapValue"]["fields"].items()})
                else:
                    toilets.append(pv(item))
            chunk_count = i + 1
        except urllib.error.HTTPError:
            break
    return toilets, chunk_count


def write_city(city_key, toilets, old_chunk_count):
    new_chunks = [toilets[i:i+CHUNK_SIZE] for i in range(0, len(toilets), CHUNK_SIZE)]
    for i, chunk in enumerate(new_chunks):
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        fs_patch(f"cities/{city_key}/chunks/{i}", body)
    for i in range(len(new_chunks), old_chunk_count):
        try:
            fs_delete(f"cities/{city_key}/chunks/{i}")
        except Exception:
            pass
    fs_patch(f"cities/{city_key}", {"fields": {
        "count": {"integerValue": str(len(toilets))},
        "chunks": {"integerValue": str(len(new_chunks))},
        "lastUpdated": {"integerValue": str(int(time.time() * 1000))},
    }})
    return len(new_chunks)


# ── Lodging ingest ──
def ingest_lodging(city_key, bbox, existing_ids):
    radius = 2500
    centers = generate_grid(bbox, radius)
    all_places = {}
    api_count = 0
    for lat, lng in centers:
        result = nearby_search(lat, lng, radius)
        api_count += 1
        for p in result.get("places", []):
            pid = p.get("id")
            if pid and pid not in all_places:
                all_places[pid] = p
        time.sleep(0.12)

    new_toilets = []
    for place in all_places.values():
        t = place_to_toilet(place, bbox)
        if in_bbox(t, bbox) and t["id"] not in existing_ids:
            new_toilets.append(t)

    return new_toilets, api_count, len(all_places)


# ── Main ──
def main():
    total_api = 0
    summaries = []

    for city_key, cfg in CITIES.items():
        bbox = {k: v for k, v in cfg.items() if k != "region"}
        region = cfg["region"]
        print(f"\n{'='*60}")
        print(f"  {city_key.upper()}")
        print(f"{'='*60}")

        # Fetch
        print(f"  Fetching...", end=" ", flush=True)
        toilets, old_chunks = fetch_city(city_key)
        before = len(toilets)
        print(f"{before} items, {old_chunks} chunks")

        # 1. bbox filter
        filtered = [t for t in toilets if in_bbox(t, bbox)]
        bbox_removed = before - len(filtered)
        print(f"  [1] bbox除外: {bbox_removed} 件")

        # 2. Tier reclassify (before lodging ingest)
        for t in filtered:
            t["tier"] = classify_tier(t, region)

        # 3. source
        for t in filtered:
            t["source"] = "google"

        # Check if lodging already exists
        existing_lodging = sum(1 for t in filtered if t.get("tier") == 3 and is_lodging(t))
        existing_ids = {t.get("id") for t in filtered if t.get("id")}

        # 4. Lodging ingest
        print(f"  [3] Lodging ingest...", end=" ", flush=True)
        new_lodging, api_count, total_found = ingest_lodging(city_key, bbox, existing_ids)
        total_api += api_count
        print(f"found {total_found}, new {len(new_lodging)}, API reqs: {api_count}")

        # Merge
        merged = filtered + new_lodging
        after = len(merged)

        # Write
        print(f"  Writing...", end=" ", flush=True)
        n_chunks = write_city(city_key, merged, old_chunks)
        print(f"{n_chunks} chunks OK")

        # Tier distribution
        tier_dist = {}
        for t in merged:
            tier_dist[t.get("tier", "?")] = tier_dist.get(t.get("tier", "?"), 0) + 1

        print(f"  ──────────────────────────")
        print(f"  総件数: {before} → {after}")
        print(f"  bbox除外: {bbox_removed}")
        print(f"  lodging追加: {len(new_lodging)}")
        for tier in sorted(tier_dist):
            pct = tier_dist[tier] / after * 100
            print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")

        summaries.append({
            "city": city_key,
            "before": before,
            "after": after,
            "bbox_removed": bbox_removed,
            "lodging_added": len(new_lodging),
            "api_reqs": api_count,
            "tiers": tier_dist,
        })

    # ── Grand Summary ──
    print(f"\n\n{'='*60}")
    print(f"  GRAND SUMMARY (7 cities)")
    print(f"{'='*60}")
    print(f"  {'City':<12} {'Before':>7} {'After':>7} {'BBox-':>6} {'Lodg+':>6}  T1    T2    T3    T4")
    print(f"  {'-'*80}")
    grand_before = grand_after = grand_bbox = grand_lodging = 0
    grand_tiers = {1:0, 2:0, 3:0, 4:0}
    for s in summaries:
        t = s["tiers"]
        print(f"  {s['city']:<12} {s['before']:>7} {s['after']:>7} {s['bbox_removed']:>6} {s['lodging_added']:>6}"
              f"  {t.get(1,0):>5} {t.get(2,0):>5} {t.get(3,0):>5} {t.get(4,0):>5}")
        grand_before += s["before"]
        grand_after += s["after"]
        grand_bbox += s["bbox_removed"]
        grand_lodging += s["lodging_added"]
        for tier in [1,2,3,4]:
            grand_tiers[tier] += t.get(tier, 0)

    print(f"  {'-'*80}")
    print(f"  {'TOTAL':<12} {grand_before:>7} {grand_after:>7} {grand_bbox:>6} {grand_lodging:>6}"
          f"  {grand_tiers[1]:>5} {grand_tiers[2]:>5} {grand_tiers[3]:>5} {grand_tiers[4]:>5}")
    print(f"\n  Total Places API requests: {total_api}")


if __name__ == "__main__":
    main()
