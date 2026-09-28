#!/usr/bin/env python3
"""Extract only public Bonsai challenge metadata from a downloaded Yukon homepage."""
import json, re, sys
from pathlib import Path
html = Path(sys.argv[1]).read_text()
found = []
def walk(value):
    if isinstance(value, dict):
        if value.get("name") == "davidtai/mlxfast-bonsai2-27b":
            keys = ("id", "name", "status", "sourceUrl", "sourceBranch", "sourceRef", "bestScore", "updatedAt")
            found.append({k: value[k] for k in keys if k in value})
        for child in value.values(): walk(child)
    elif isinstance(value, list):
        for child in value: walk(child)
for raw in re.findall(r'self\.__next_f\.push\((\[.*?\])\)</script>', html):
    try: stream = json.loads(raw)[1]
    except (ValueError, IndexError): continue
    for match in re.finditer(r'"benchmarks":(\[)', stream):
        try: benchmarks, _ = json.JSONDecoder().raw_decode(stream[match.start(1):])
        except ValueError: continue
        walk(benchmarks)
if len(found) != 1: raise SystemExit(f"Expected one challenge record, got {len(found)}")
print(json.dumps({"retrieved_utc_date": "2026-09-28", "source": "https://www.yukon.org/", "challenge": found[0]}, indent=2))
