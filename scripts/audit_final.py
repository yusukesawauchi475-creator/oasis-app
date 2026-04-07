#!/usr/bin/env python3
"""Audit Manhattan toilet data from Firestore (oasis-bde20) via gcloud auth."""
import json
import re
import subprocess
import urllib.request

PROJECT = "oasis-bde20"
TOKEN = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

# Manhattan bbox: generous bounds around center 40.754, -74.003
BBOX = {"lat_min": 40.680, "lat_max": 40.882, "lng_min": -74.047, "lng_max": -73.907}


def api_get(path):
    url = f"{BASE}/{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def pv(v):
    """Parse Firestore value."""
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return float(v["doubleValue"])
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "arrayValue" in v: return [pv(x) for x in v["arrayValue"].get("values", [])]
    if "mapValue" in v: return {k: pv(fv) for k, fv in v["mapValue"].get("fields", {}).items()}
    return str(v)


def parse_toilet(raw_item):
    """Parse a raw Firestore array item into a toilet dict."""
    if "mapValue" in raw_item:
        fields = raw_item["mapValue"].get("fields", {})
        return {k: pv(fv) for k, fv in fields.items()}
    return pv(raw_item)


def english_ratio(name):
    if not name: return 0
    alpha = [c for c in name if c.isalpha()]
    if not alpha: return 0
    ascii_a = [c for c in alpha if ord(c) < 128]
    return len(ascii_a) / len(alpha)


def is_outside_bbox(t):
    lat, lng = t.get("lat"), t.get("lng")
    if lat is None or lng is None: return True
    return lat < BBOX["lat_min"] or lat > BBOX["lat_max"] or lng < BBOX["lng_min"] or lng > BBOX["lng_max"]


def hours_to_str(hours):
    """Convert hours field (string, list, or None) to a single string."""
    if not hours: return ""
    if isinstance(hours, str): return hours
    if isinstance(hours, list): return " | ".join(str(h) for h in hours if h)
    return str(hours)


def has_english_hours(hours):
    h = hours_to_str(hours)
    if not h: return False
    pats = [
        r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        r'\b(Open|Closed|Hours|AM|PM|am|pm|24\s*hours|24/7)\b',
        r'\d{1,2}:\d{2}\s*(AM|PM|am|pm)',
    ]
    return any(re.search(p, h) for p in pats)


def main():
    print("Fetching Manhattan chunks from Firestore...\n")
    all_toilets = []

    for i in range(10):
        try:
            raw = api_get(f"cities/manhattan/chunks/{i}")
            fields = raw.get("fields", {})
            toilets_raw = fields.get("toilets", {}).get("arrayValue", {}).get("values", [])
            toilets = [parse_toilet(t) for t in toilets_raw]
            print(f"  chunk {i}: {len(toilets)} items")
            all_toilets.extend(toilets)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
            raise

    print(f"\n{'='*60}")
    print(f"TOTAL MANHATTAN TOILETS: {len(all_toilets)}")
    print(f"{'='*60}")

    # Sample
    if all_toilets:
        print(f"\nSample: {json.dumps(all_toilets[0], ensure_ascii=False, default=str)[:300]}")

    # ─── [1] name英字50%以上 ───
    eng_names = [t for t in all_toilets if english_ratio(t.get("name", "")) >= 0.5]
    non_eng = [t for t in all_toilets if english_ratio(t.get("name", "")) < 0.5]
    print(f"\n[1] name英字50%以上: {len(eng_names)} 件 / {len(all_toilets)} 件 ({len(eng_names)/len(all_toilets)*100:.1f}%)")
    print("    サンプル (英字50%+):")
    for t in eng_names[:5]:
        r = english_ratio(t.get("name", ""))
        print(f"      {t.get('name')} ({r*100:.0f}%, cat={t.get('cat')}, tier={t.get('tier')})")
    if non_eng:
        print("    サンプル (英字50%未満):")
        for t in non_eng[:5]:
            r = english_ratio(t.get("name", ""))
            print(f"      {t.get('name')} ({r*100:.0f}%, cat={t.get('cat')}, tier={t.get('tier')})")

    # ─── [2] bbox外 ───
    outside = [t for t in all_toilets if is_outside_bbox(t)]
    print(f"\n[2] bbox外: {len(outside)} 件")
    print(f"    bbox: lat {BBOX['lat_min']}–{BBOX['lat_max']}, lng {BBOX['lng_min']}–{BBOX['lng_max']}")
    if outside:
        for t in outside[:20]:
            print(f"    {t.get('name','?')}: ({t.get('lat')}, {t.get('lng')})")
    else:
        print("    全件bbox内 ✓")

    # ─── [3] tier=4 & cat=Public ───
    t4pub = [t for t in all_toilets if t.get("tier") == 4 and t.get("cat") == "Public"]
    print(f"\n[3] tier=4 & cat=Public (tier割り当てミスの可能性): {len(t4pub)} 件")
    for t in t4pub[:20]:
        print(f"    {t.get('name','?')} (id={t.get('id','?')}, free={t.get('free')}, hours={t.get('hours','N/A')})")

    # ─── [4] hours英語表記 ───
    with_hours = [t for t in all_toilets if t.get("hours")]
    eng_hours = [t for t in all_toilets if has_english_hours(t.get("hours"))]
    print(f"\n[4] hours英語表記: {len(eng_hours)} 件 / hours有り {len(with_hours)} 件")
    for t in eng_hours[:15]:
        print(f"    {t.get('name','?')}: \"{hours_to_str(t.get('hours'))}\"")

    # ─── SUMMARY ───
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")
    print(f"  総件数:              {len(all_toilets)}")
    print(f"  [1] 英字名50%+:     {len(eng_names)} ({len(eng_names)/len(all_toilets)*100:.1f}%)")
    print(f"  [2] bbox外:         {len(outside)}")
    print(f"  [3] T4+Public:      {len(t4pub)}")
    print(f"  [4] 英語hours:      {len(eng_hours)}")

    # Distributions
    tier_dist = {}
    for t in all_toilets:
        k = str(t.get("tier", "none"))
        tier_dist[k] = tier_dist.get(k, 0) + 1
    print(f"\n  Tier分布: {json.dumps(tier_dist, sort_keys=True)}")

    cat_dist = {}
    for t in all_toilets:
        k = t.get("cat", "none")
        cat_dist[k] = cat_dist.get(k, 0) + 1
    print(f"  Cat分布:  {json.dumps(cat_dist, sort_keys=True)}")

    src_dist = {}
    for t in all_toilets:
        k = t.get("source", "none")
        src_dist[k] = src_dist.get(k, 0) + 1
    print(f"  Source分布: {json.dumps(src_dist, sort_keys=True)}")

    free_dist = {}
    for t in all_toilets:
        k = str(t.get("free", "none"))
        free_dist[k] = free_dist.get(k, 0) + 1
    print(f"  Free分布: {json.dumps(free_dist, sort_keys=True)}")


if __name__ == "__main__":
    main()
