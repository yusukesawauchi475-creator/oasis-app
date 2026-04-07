#!/usr/bin/env python3
"""Fix Manhattan Firestore data: bbox filter, tier reclassify, add source."""
import json
import math
import re
import subprocess
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

BBOX = {"lat_min": 40.680, "lat_max": 40.882, "lng_min": -74.047, "lng_max": -73.907}
CHUNK_SIZE = 800


def api_get(path):
    url = f"{BASE}/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_patch(path, body):
    url = f"{BASE}/{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_delete(path):
    url = f"{BASE}/{path}"
    req = urllib.request.Request(url, headers=HEADERS, method="DELETE")
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


def parse_toilet(raw):
    if "mapValue" in raw:
        return {k: pv(fv) for k, fv in raw["mapValue"].get("fields", {}).items()}
    return pv(raw)


def to_firestore_value(val):
    """Convert Python value to Firestore REST value."""
    if val is None:
        return {"nullValue": None}
    if isinstance(val, bool):
        return {"booleanValue": val}
    if isinstance(val, int):
        return {"integerValue": str(val)}
    if isinstance(val, float):
        return {"doubleValue": val}
    if isinstance(val, str):
        return {"stringValue": val}
    if isinstance(val, list):
        if not val:
            return {"arrayValue": {}}
        return {"arrayValue": {"values": [to_firestore_value(x) for x in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {k: to_firestore_value(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def is_in_bbox(t):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None:
        return False
    return (BBOX["lat_min"] <= lat <= BBOX["lat_max"] and
            BBOX["lng_min"] <= lng <= BBOX["lng_max"])


def classify_tier(t):
    # isPartner=true → T1
    if t.get("isPartner"):
        return 1
    cat = t.get("cat", "")
    name = (t.get("name") or "").lower()
    if cat == "Public":
        return 1
    if cat == "Transit":
        return 2
    if cat == "Store":
        if re.search(r'\bhotels?\b|\bmotels?\b', name):
            return 3
        return 4
    # Fallback
    return 4


def main():
    # ── Phase 1: Fetch all chunks ──
    print("Phase 1: Fetching Manhattan chunks...")
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
            if e.code == 404:
                break
            raise

    print(f"  Total fetched: {len(all_toilets)}")

    # ── Phase 2: Apply fixes ──
    print("\nPhase 2: Applying fixes...")

    # Fix 1: bbox filter
    before = len(all_toilets)
    all_toilets = [t for t in all_toilets if is_in_bbox(t)]
    removed = before - len(all_toilets)
    print(f"  [1] bbox外除外: {removed} 件削除 → {len(all_toilets)} 件残")

    # Fix 2: Tier reclassify
    tier_changes = {"upgraded": 0, "downgraded": 0, "unchanged": 0}
    for t in all_toilets:
        old_tier = t.get("tier")
        new_tier = classify_tier(t)
        if old_tier != new_tier:
            if new_tier < (old_tier or 99):
                tier_changes["upgraded"] += 1
            else:
                tier_changes["downgraded"] += 1
        else:
            tier_changes["unchanged"] += 1
        t["tier"] = new_tier

    print(f"  [2] Tier再分類: upgraded={tier_changes['upgraded']}, "
          f"downgraded={tier_changes['downgraded']}, unchanged={tier_changes['unchanged']}")

    # Fix 3: Add source='google'
    source_added = sum(1 for t in all_toilets if t.get("source") != "google")
    for t in all_toilets:
        t["source"] = "google"
    print(f"  [3] source='google' 追加: {source_added} 件")

    # ── Phase 3: Tier summary ──
    tier_dist = {}
    for t in all_toilets:
        tier_dist[t["tier"]] = tier_dist.get(t["tier"], 0) + 1

    cat_dist = {}
    for t in all_toilets:
        cat_dist[t.get("cat", "?")] = cat_dist.get(t.get("cat", "?"), 0) + 1

    print(f"\n  修正後件数: {len(all_toilets)}")
    print(f"  Tier内訳:")
    for tier in sorted(tier_dist):
        print(f"    T{tier}: {tier_dist[tier]}")
    print(f"  Cat内訳: {json.dumps(cat_dist, sort_keys=True)}")

    # ── Phase 4: Write back to Firestore ──
    print("\nPhase 3: Writing back to Firestore...")

    # Split into chunks of CHUNK_SIZE
    new_chunks = []
    for i in range(0, len(all_toilets), CHUNK_SIZE):
        new_chunks.append(all_toilets[i:i + CHUNK_SIZE])

    print(f"  New chunk count: {len(new_chunks)} (was {chunk_count})")

    for i, chunk_data in enumerate(new_chunks):
        print(f"  Writing chunk {i} ({len(chunk_data)} items)...", end=" ", flush=True)
        fs_toilets = [to_firestore_value(t) for t in chunk_data]
        body = {
            "fields": {
                "toilets": {
                    "arrayValue": {
                        "values": fs_toilets
                    }
                }
            }
        }
        api_patch(f"cities/manhattan/chunks/{i}", body)
        print("OK")

    # Delete extra chunks if we now have fewer
    for i in range(len(new_chunks), chunk_count):
        print(f"  Deleting chunk {i} (no longer needed)...", end=" ", flush=True)
        api_delete(f"cities/manhattan/chunks/{i}")
        print("OK")

    # Update manhattan metadata doc
    print("  Updating metadata...", end=" ", flush=True)
    import time
    meta_body = {
        "fields": {
            "count": {"integerValue": str(len(all_toilets))},
            "chunks": {"integerValue": str(len(new_chunks))},
            "lastUpdated": {"integerValue": str(int(time.time() * 1000))}
        }
    }
    api_patch("cities/manhattan", meta_body)
    print("OK")

    # ── Final Report ──
    print(f"\n{'='*60}")
    print("FINAL REPORT")
    print(f"{'='*60}")
    print(f"  修正前件数:   {before}")
    print(f"  bbox外除外:   -{removed}")
    print(f"  修正後件数:   {len(all_toilets)}")
    print(f"  チャンク数:   {len(new_chunks)}")
    print(f"")
    print(f"  Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(all_toilets) * 100
        print(f"    T{tier}: {tier_dist[tier]:>6} ({pct:.1f}%)")
    print(f"")
    print(f"  source: 全件 'google' ✓")


if __name__ == "__main__":
    main()
