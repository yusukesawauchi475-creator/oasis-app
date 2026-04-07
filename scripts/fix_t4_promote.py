#!/usr/bin/env python3
"""Promote known convenience/pharmacy/supermarket chains from T4 to T3."""
import json
import re
import subprocess
import time
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"
CHUNK_SIZE = 800

# Chains to promote to T3
PROMOTE_PATTERN = re.compile(
    r'\b(7[\-\s]?eleven|cvs|walgreens?|duane\s*reade|rite\s*aid|'
    r'whole\s*foods|trader\s*joe\'?s|target|walmart|starbucks)\b',
    re.IGNORECASE
)

def fs_get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def fs_patch(path, body):
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

def should_promote(t):
    name = t.get("name") or ""
    return bool(PROMOTE_PATTERN.search(name))


def main():
    # Fetch
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
            old_chunks = i + 1
        except urllib.error.HTTPError:
            break
    print(f"  Total: {len(all_toilets)}")

    # Promote
    promoted = []
    for t in all_toilets:
        if t.get("tier") == 4 and should_promote(t):
            t["tier"] = 3
            promoted.append(t)

    print(f"\nT4→T3 昇格: {len(promoted)} 件")

    # Breakdown by chain
    chain_counts = {}
    for t in promoted:
        m = PROMOTE_PATTERN.search(t.get("name", ""))
        chain = m.group(1).lower() if m else "?"
        chain_counts[chain] = chain_counts.get(chain, 0) + 1
    for chain, count in sorted(chain_counts.items(), key=lambda x: -x[1]):
        print(f"    {chain}: {count}")

    # Write back
    new_chunks = [all_toilets[i:i+CHUNK_SIZE] for i in range(0, len(all_toilets), CHUNK_SIZE)]
    print(f"\nWriting {len(new_chunks)} chunks...")
    for i, chunk in enumerate(new_chunks):
        print(f"  chunk {i} ({len(chunk)})...", end=" ", flush=True)
        body = {"fields": {"toilets": {"arrayValue": {"values": [to_fv(t) for t in chunk]}}}}
        fs_patch(f"cities/manhattan/chunks/{i}", body)
        print("OK")

    fs_patch("cities/manhattan", {"fields": {
        "count": {"integerValue": str(len(all_toilets))},
        "chunks": {"integerValue": str(len(new_chunks))},
        "lastUpdated": {"integerValue": str(int(time.time() * 1000))},
    }})

    # Report
    tier_dist = {}
    for t in all_toilets:
        tier_dist[t.get("tier", "?")] = tier_dist.get(t.get("tier", "?"), 0) + 1

    print(f"\n{'='*60}")
    print("REPORT")
    print(f"{'='*60}")
    print(f"  T3追加(昇格)件数: {len(promoted)}")
    print(f"  T4残件数:         {tier_dist.get(4, 0)}")
    print(f"\n  全Tier内訳:")
    for tier in sorted(tier_dist):
        pct = tier_dist[tier] / len(all_toilets) * 100
        print(f"    T{tier}: {tier_dist[tier]:>5} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
