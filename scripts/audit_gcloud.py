#!/usr/bin/env python3
"""Audit Manhattan data via Firestore REST API with gcloud auth."""
import json
import re
import subprocess
import urllib.request

PROJECT = "oasis-bde20"

# Get token from gcloud
token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

BBOX = {"lat_min": 40.680, "lat_max": 40.880, "lng_min": -74.050, "lng_max": -73.900}


def api_get(path):
    url = f"{BASE}/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_list(collection, page_size=300, page_token=None):
    url = f"{BASE}/{collection}?pageSize={page_size}"
    if page_token:
        url += f"&pageToken={page_token}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def parse_value(v):
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return float(v["doubleValue"])
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "arrayValue" in v:
        return [parse_value(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v:
        return {k: parse_value(fv) for k, fv in v["mapValue"].get("fields", {}).items()}
    return str(v)


def parse_doc(doc):
    fields = doc.get("fields", {})
    return {k: parse_value(v) for k, v in fields.items()}


def english_ratio(name):
    if not name: return 0
    alpha = [c for c in name if c.isalpha()]
    if not alpha: return 0
    ascii_alpha = [c for c in alpha if ord(c) < 128]
    return len(ascii_alpha) / len(alpha)


def is_outside_bbox(t):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None: return True
    return lat < BBOX["lat_min"] or lat > BBOX["lat_max"] or lng < BBOX["lng_min"] or lng > BBOX["lng_max"]


def has_english_hours(hours):
    if not hours or not isinstance(hours, str): return False
    pats = [
        r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        r'\b(Open|Closed|Hours|AM|PM|am|pm|24\s*hours|24/7)\b',
        r'\d{1,2}:\d{2}\s*(AM|PM|am|pm)',
    ]
    return any(re.search(p, hours) for p in pats)


def main():
    print("Listing toilets collection docs...")
    all_doc_ids = []
    page_token = None
    while True:
        result = api_list("toilets", page_size=300, page_token=page_token)
        docs = result.get("documents", [])
        for d in docs:
            doc_id = d["name"].split("/")[-1]
            all_doc_ids.append(doc_id)
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    print(f"Total docs in collection: {len(all_doc_ids)}")
    manhattan_ids = [x for x in all_doc_ids if "manhattan" in x.lower()]
    print(f"Manhattan docs: {manhattan_ids}")

    # Also show all doc IDs for reference
    print(f"All doc IDs: {all_doc_ids[:30]}{'...' if len(all_doc_ids) > 30 else ''}")

    # Fetch manhattan docs and extract toilets
    all_toilets = []
    for doc_id in manhattan_ids:
        print(f"\nFetching {doc_id}...")
        raw = api_get(f"toilets/{doc_id}")
        data = parse_doc(raw)
        keys = list(data.keys())
        print(f"  Fields: {keys}")

        items = data.get("items") or data.get("data") or data.get("toilets") or []
        if isinstance(items, list):
            print(f"  Items: {len(items)}")
            all_toilets.extend(items)
        else:
            print(f"  Not a list, type: {type(items)}")

    if not all_toilets:
        print("\nNo toilet data found!")
        # Show sample of first doc to understand structure
        if all_doc_ids:
            raw = api_get(f"toilets/{all_doc_ids[0]}")
            data = parse_doc(raw)
            sample_str = json.dumps(data, ensure_ascii=False, default=str)
            print(f"Sample doc ({all_doc_ids[0]}): {sample_str[:1000]}")
        return

    # Sample
    print(f"\nSample toilet: {json.dumps(all_toilets[0], ensure_ascii=False, default=str)}")

    print(f"\n{'='*60}")
    print(f"TOTAL MANHATTAN TOILETS: {len(all_toilets)}")
    print(f"{'='*60}\n")

    # [1] English name >= 50%
    eng_names = [t for t in all_toilets if english_ratio(t.get("name", "")) >= 0.5]
    print(f"[1] name英字50%以上: {eng_names.__len__()} 件 / {len(all_toilets)} 件 ({len(eng_names)/len(all_toilets)*100:.1f}%)")
    for t in eng_names[:8]:
        print(f"    {t.get('name')} ({english_ratio(t.get('name',''))*100:.0f}%, cat={t.get('cat')}, tier={t.get('tier')})")

    # [2] Outside bbox
    outside = [t for t in all_toilets if is_outside_bbox(t)]
    print(f"\n[2] bbox外: {len(outside)} 件  (lat {BBOX['lat_min']}–{BBOX['lat_max']}, lng {BBOX['lng_min']}–{BBOX['lng_max']})")
    for t in outside[:15]:
        print(f"    {t.get('name','?')}: ({t.get('lat')}, {t.get('lng')})")

    # [3] tier=4 & cat=Public
    t4pub = [t for t in all_toilets if t.get("tier") == 4 and t.get("cat") == "Public"]
    print(f"\n[3] tier=4 & cat=Public: {len(t4pub)} 件")
    for t in t4pub[:15]:
        print(f"    {t.get('name','?')} (id={t.get('id','?')})")

    # [4] English hours
    with_hours = [t for t in all_toilets if t.get("hours")]
    eng_hours = [t for t in all_toilets if has_english_hours(t.get("hours"))]
    print(f"\n[4] hours英語表記: {len(eng_hours)} 件 / hours有り {len(with_hours)} 件")
    for t in eng_hours[:10]:
        print(f"    {t.get('name','?')}: \"{t.get('hours')}\"")

    # Summary
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"  総件数:              {len(all_toilets)}")
    print(f"  [1] 英字名50%+:     {len(eng_names)} ({len(eng_names)/len(all_toilets)*100:.1f}%)")
    print(f"  [2] bbox外:         {len(outside)}")
    print(f"  [3] T4+Public:      {len(t4pub)}")
    print(f"  [4] 英語hours:      {len(eng_hours)}")

    tier_dist = {}
    for t in all_toilets:
        k = t.get("tier", "none")
        tier_dist[k] = tier_dist.get(k, 0) + 1
    print(f"\n  Tier分布: {json.dumps(tier_dist)}")

    cat_dist = {}
    for t in all_toilets:
        k = t.get("cat", "none")
        cat_dist[k] = cat_dist.get(k, 0) + 1
    print(f"  Cat分布:  {json.dumps(cat_dist)}")

    src_dist = {}
    for t in all_toilets:
        k = t.get("source", "none")
        src_dist[k] = src_dist.get(k, 0) + 1
    print(f"  Source分布: {json.dumps(src_dist)}")


if __name__ == "__main__":
    main()
