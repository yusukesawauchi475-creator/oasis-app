#!/usr/bin/env python3
"""Fix T3 classification for Manhattan: lodging detection."""
import json
import re
import subprocess
import time
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

HOTEL_NAMES = re.compile(
    r'\b(hilton|marriott|hyatt|sheraton|westin|ritz|four\s*seasons|w\s+hotel|kimpton|'
    r'intercontinental|holiday\s*inn|best\s*western|inn|suites|lodge|resort|hotel|motel)\b',
    re.IGNORECASE
)


def api_get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def pv(v):
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return float(v["doubleValue"])
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "arrayValue" in v: return [pv(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v: return {k: pv(fv) for k, fv in v["mapValue"].get("fields", {}).items()}
    return str(v)


def parse_toilet(raw):
    if "mapValue" in raw:
        return {k: pv(fv) for k, fv in raw["mapValue"].get("fields", {}).items()}
    return pv(raw)


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


def is_lodging(t):
    """Check if toilet is a lodging/hotel."""
    # Check types array first
    types = t.get("types")
    if isinstance(types, list):
        for tp in types:
            if isinstance(tp, str) and tp.lower() in ("lodging", "hotel"):
                return True
    # Fallback: name matching
    name = t.get("name") or ""
    return bool(HOTEL_NAMES.search(name))


def classify_tier(t):
    if t.get("isPartner"):
        return 1
    cat = t.get("cat", "")
    if cat == "Public":
        return 1
    if cat == "Transit":
        return 2
    if cat == "Store":
        if is_lodging(t):
            return 3
        return 4
    return 4


def main():
    # ── Fetch ──
    print("Fetching Manhattan chunks...")
    all_toilets = []
    chunk_count = 0
    for i in range(20):
        try:
            raw = api_get(f"cities/manhattan/chunks/{i}")
            vals = raw.get("fields", {}).get("toilets", {}).get("arrayValue", {}).get("values", [])
            toilets = [parse_toilet(t) for t in vals]
            print(f"  chunk {i}: {len(toilets)} items")
            all_toilets.extend(toilets)
            chunk_count = i + 1
        except urllib.error.HTTPError as e:
            if e.code == 404: break
            raise

    print(f"  Total: {len(all_toilets)}")

    # ── Check for types field ──
    has_types = sum(1 for t in all_toilets if t.get("types"))
    print(f"\n  'types'フィールド有り: {has_types} 件")

    # ── Reclassify ──
    print("\nReclassifying tiers...")
    t3_list = []
    changes = 0
    for t in all_toilets:
        old = t.get("tier")
        new = classify_tier(t)
        if old != new:
            changes += 1
        t["tier"] = new
        if new == 3:
            t3_list.append(t)

    # ── Report ──
    tier_dist = {}
    for t in all_toilets:
        tier_dist[t["tier"]] = tier_dist.get(t["tier"], 0) + 1

    print(f"\n  変更件数: {changes}")
    print(f"  Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(all_toilets) * 100
        print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")

    print(f"\n  T3件数: {len(t3_list)}")
    print(f"  T3例:")
    for t in t3_list[:5]:
        print(f"    {t.get('name')} ({t.get('lat')}, {t.get('lng')})")

    if len(t3_list) > 5:
        print(f"  ... 他 {len(t3_list) - 5} 件")

    # ── Write back ──
    print("\nWriting back to Firestore...")
    CHUNK_SIZE = 800
    new_chunks = [all_toilets[i:i+CHUNK_SIZE] for i in range(0, len(all_toilets), CHUNK_SIZE)]

    for i, chunk in enumerate(new_chunks):
        print(f"  chunk {i} ({len(chunk)} items)...", end=" ", flush=True)
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        api_patch(f"cities/manhattan/chunks/{i}", body)
        print("OK")

    # Delete extra
    for i in range(len(new_chunks), chunk_count):
        print(f"  Deleting chunk {i}...")
        urllib.request.Request(f"{BASE}/cities/manhattan/chunks/{i}", headers=HEADERS, method="DELETE")

    # Update metadata
    meta = {
        "fields": {
            "count": {"integerValue": str(len(all_toilets))},
            "chunks": {"integerValue": str(len(new_chunks))},
            "lastUpdated": {"integerValue": str(int(time.time() * 1000))}
        }
    }
    api_patch("cities/manhattan", meta)
    print("  Metadata updated.")

    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
