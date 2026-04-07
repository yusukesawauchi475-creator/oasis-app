#!/usr/bin/env python3
"""Remove bbox-outside lodging from Manhattan Firestore data."""
import json
import subprocess
import time
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

# Tightened bbox: lat_min 40.681 (exclusive of 40.680 grey zone)
BBOX = {"lat_min": 40.681, "lat_max": 40.882, "lng_min": -74.047, "lng_max": -73.907}
CHUNK_SIZE = 800


def fs_get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fs_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fs_delete(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS, method="DELETE")
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

def in_bbox(t):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None: return False
    return BBOX["lat_min"] <= lat <= BBOX["lat_max"] and BBOX["lng_min"] <= lng <= BBOX["lng_max"]


def main():
    # Fetch all chunks
    print("Fetching chunks...")
    all_toilets = []
    old_chunks = 0
    for i in range(20):
        try:
            raw = fs_get(f"cities/manhattan/chunks/{i}")
            vals = raw["fields"]["toilets"]["arrayValue"]["values"]
            for item in vals:
                if "mapValue" in item:
                    all_toilets.append({k: pv(fv) for k, fv in item["mapValue"]["fields"].items()})
                else:
                    all_toilets.append(pv(item))
            print(f"  chunk {i}: {len(vals)} items")
            old_chunks = i + 1
        except urllib.error.HTTPError:
            break

    total_before = len(all_toilets)
    print(f"  Total: {total_before}")

    # Find bbox-outside items
    outside = [t for t in all_toilets if not in_bbox(t)]
    outside_lodging = [t for t in outside if t.get("tier") == 3]
    outside_other = [t for t in outside if t.get("tier") != 3]

    print(f"\nbbox外: {len(outside)} 件 (T3: {len(outside_lodging)}, 他: {len(outside_other)})")
    for t in outside[:10]:
        print(f"  {t.get('name')}: ({t.get('lat')}, {t.get('lng')}) tier={t.get('tier')}")

    # Filter
    kept = [t for t in all_toilets if in_bbox(t)]
    removed = total_before - len(kept)
    print(f"\n削除: {removed} 件 → 残: {len(kept)} 件")

    # Write back
    new_chunks = [kept[i:i+CHUNK_SIZE] for i in range(0, len(kept), CHUNK_SIZE)]
    print(f"\nWriting {len(new_chunks)} chunks...")
    for i, chunk in enumerate(new_chunks):
        print(f"  chunk {i} ({len(chunk)})...", end=" ", flush=True)
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        fs_patch(f"cities/manhattan/chunks/{i}", body)
        print("OK")

    for i in range(len(new_chunks), old_chunks):
        print(f"  Deleting chunk {i}...", end=" ", flush=True)
        fs_delete(f"cities/manhattan/chunks/{i}")
        print("OK")

    fs_patch("cities/manhattan", {"fields": {
        "count": {"integerValue": str(len(kept))},
        "chunks": {"integerValue": str(len(new_chunks))},
        "lastUpdated": {"integerValue": str(int(time.time() * 1000))},
    }})

    # Report
    t3 = [t for t in kept if t.get("tier") == 3]
    # Pick T3 examples near Midtown (lat ~40.75-40.76)
    midtown = sorted(t3, key=lambda t: abs((t.get("lat") or 0) - 40.755) + abs((t.get("lng") or 0) + 73.985))

    tier_dist = {}
    for t in kept:
        tier_dist[t.get("tier", "?")] = tier_dist.get(t.get("tier", "?"), 0) + 1

    print(f"\n{'='*60}")
    print("REPORT")
    print(f"{'='*60}")
    print(f"  削除件数:     {removed}")
    print(f"  修正後総件数: {len(kept)}")
    print(f"  修正後T3:     {len(t3)}")
    print(f"\n  Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(kept) * 100
        print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")
    print(f"\n  T3 例 (Manhattan中心部):")
    for t in midtown[:3]:
        print(f"    {t['name']} ({t['lat']}, {t['lng']})")


if __name__ == "__main__":
    main()
