#!/usr/bin/env python3
"""Audit Manhattan toilet data from Firestore (oasis-bde20)."""

import json
import re
import urllib.request

PROJECT = "oasis-bde20"
API_KEY = "AIzaSyDXQabNFmpISVQ4O_yCP6dTyx-UC_uGQLw"
BASE = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents"

# Manhattan bbox from SSOT (center 40.754, -74.003) with reasonable bounds
MANHATTAN_BBOX = {
    "lat_min": 40.680,
    "lat_max": 40.880,
    "lng_min": -74.050,
    "lng_max": -73.900,
}


def fetch_doc(path):
    url = f"{BASE}/{path}?key={API_KEY}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return None


def parse_value(v):
    """Parse a Firestore REST API value."""
    if "stringValue" in v:
        return v["stringValue"]
    if "integerValue" in v:
        return int(v["integerValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "booleanValue" in v:
        return v["booleanValue"]
    if "nullValue" in v:
        return None
    if "arrayValue" in v:
        vals = v["arrayValue"].get("values", [])
        return [parse_value(x) for x in vals]
    if "mapValue" in v:
        fields = v["mapValue"].get("fields", {})
        return {k: parse_value(fv) for k, fv in fields.items()}
    return str(v)


def extract_toilets(doc):
    """Extract toilet array from a Firestore document."""
    if not doc or "fields" not in doc:
        return []
    fields = doc["fields"]
    # Try common field names
    for key in ["toilets", "data", "items", "locations"]:
        if key in fields:
            return parse_value(fields[key]) if isinstance(parse_value(fields[key]), list) else []
    # If there's an array field, use it
    for key, val in fields.items():
        parsed = parse_value(val)
        if isinstance(parsed, list):
            return parsed
    return []


def english_ratio(name):
    if not name:
        return 0
    ascii_chars = sum(1 for c in name if c.isascii() and c.isalpha())
    total_alpha = sum(1 for c in name if c.isalpha())
    if total_alpha == 0:
        return 0
    return ascii_chars / total_alpha


def is_outside_bbox(t):
    lat = t.get("lat")
    lng = t.get("lng")
    if lat is None or lng is None:
        return True
    return (lat < MANHATTAN_BBOX["lat_min"] or lat > MANHATTAN_BBOX["lat_max"] or
            lng < MANHATTAN_BBOX["lng_min"] or lng > MANHATTAN_BBOX["lng_max"])


def has_english_hours(t):
    hours = t.get("hours")
    if not hours or not isinstance(hours, str):
        return False
    # Check for English patterns in hours
    eng_patterns = [
        r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b',
        r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
        r'\b(Open|Closed|Hours|AM|PM|am|pm)\b',
        r'\b(24\s*hours|24/7)\b',
        r'\d{1,2}:\d{2}\s*(AM|PM|am|pm)',
    ]
    for pat in eng_patterns:
        if re.search(pat, hours):
            return True
    return False


def main():
    all_toilets = []

    # Fetch chunks: manhattan_chunk_0, manhattan_chunk_1, ...
    print("Fetching Manhattan chunks from Firestore...")
    for i in range(20):  # Try up to 20 chunks
        doc = fetch_doc(f"toilets/manhattan_chunk_{i}")
        if doc is None:
            print(f"  chunk_{i}: not found (stopping)")
            break
        toilets = extract_toilets(doc)
        print(f"  chunk_{i}: {len(toilets)} toilets")
        all_toilets.extend(toilets)

    if not all_toilets:
        # Try without chunk suffix
        print("\nTrying 'toilets/manhattan' (no chunks)...")
        doc = fetch_doc("toilets/manhattan")
        if doc:
            all_toilets = extract_toilets(doc)
            print(f"  Found {len(all_toilets)} toilets")

    if not all_toilets:
        # List all documents in toilets collection
        print("\nListing toilets collection...")
        url = f"{BASE}/toilets?key={API_KEY}&pageSize=100"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                docs = data.get("documents", [])
                manhattan_docs = [d for d in docs if "manhattan" in d.get("name", "").lower()]
                print(f"  Found {len(manhattan_docs)} manhattan docs out of {len(docs)} total")
                for d in manhattan_docs:
                    name = d["name"].split("/")[-1]
                    print(f"    - {name}")
                for d in docs[:5]:
                    name = d["name"].split("/")[-1]
                    print(f"    [sample] {name}")
        except Exception as e:
            print(f"  Error: {e}")
        return

    print(f"\n{'='*60}")
    print(f"TOTAL MANHATTAN TOILETS: {len(all_toilets)}")
    print(f"{'='*60}\n")

    # --- Audit 1: English name ratio > 50% ---
    english_names = []
    for t in all_toilets:
        name = t.get("name", "")
        if english_ratio(name) >= 0.5:
            english_names.append(t)

    print(f"[1] name英字50%以上: {len(english_names)} 件 / {len(all_toilets)} 件")
    print(f"    割合: {len(english_names)/len(all_toilets)*100:.1f}%")
    # Sample
    for t in english_names[:5]:
        print(f"    例: {t.get('name')} (ratio={english_ratio(t.get('name','')):.0%})")

    # --- Audit 2: Outside Manhattan bbox ---
    outside = [t for t in all_toilets if is_outside_bbox(t)]
    print(f"\n[2] bbox外 (lat:{MANHATTAN_BBOX['lat_min']}-{MANHATTAN_BBOX['lat_max']}, "
          f"lng:{MANHATTAN_BBOX['lng_min']}-{MANHATTAN_BBOX['lng_max']}): {len(outside)} 件")
    for t in outside[:10]:
        print(f"    {t.get('name','?')}: ({t.get('lat')}, {t.get('lng')})")

    # --- Audit 3: tier=4 AND cat=Public ---
    tier4_public = [t for t in all_toilets if t.get("tier") == 4 and t.get("cat") == "Public"]
    print(f"\n[3] tier=4 & cat=Public (tier割り当てミスの可能性): {len(tier4_public)} 件")
    for t in tier4_public[:10]:
        print(f"    {t.get('name','?')} (id={t.get('id','?')})")

    # --- Audit 4: English hours ---
    eng_hours = [t for t in all_toilets if has_english_hours(t)]
    has_hours = [t for t in all_toilets if t.get("hours")]
    print(f"\n[4] hours英語表記: {len(eng_hours)} 件 / hours有り{len(has_hours)} 件")
    for t in eng_hours[:10]:
        print(f"    {t.get('name','?')}: \"{t.get('hours')}\"")

    # --- Summary ---
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  総件数:              {len(all_toilets)}")
    print(f"  [1] 英字名50%+:     {len(english_names)} ({len(english_names)/len(all_toilets)*100:.1f}%)")
    print(f"  [2] bbox外:         {len(outside)}")
    print(f"  [3] T4+Public:      {len(tier4_public)}")
    print(f"  [4] 英語hours:      {len(eng_hours)}")


if __name__ == "__main__":
    main()
