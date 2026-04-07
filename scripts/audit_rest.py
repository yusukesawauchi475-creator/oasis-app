#!/usr/bin/env python3
"""Audit Manhattan data via Firestore REST API (runQuery)."""
import json
import re
import urllib.request

PROJECT = "oasis-bde20"
API_KEY = "AIzaSyDXQabNFmpISVQ4O_yCP6dTyx-UC_uGQLw"
URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT}/databases/(default)/documents:runQuery?key={API_KEY}"

# Query all docs in 'toilets' collection
body = json.dumps({
    "structuredQuery": {
        "from": [{"collectionId": "toilets"}],
        "limit": 100
    }
}).encode()

req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        for item in data:
            doc = item.get("document", {})
            name = doc.get("name", "").split("/")[-1]
            fields = doc.get("fields", {})
            field_keys = list(fields.keys())
            # Count items in array fields
            for k, v in fields.items():
                if "arrayValue" in v:
                    count = len(v["arrayValue"].get("values", []))
                    print(f"  {name}: field '{k}' has {count} items")
                    break
            else:
                print(f"  {name}: fields={field_keys}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
