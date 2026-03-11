#!/usr/bin/env python3
"""Split a timestamps JSON list into N parts.
Usage: split_timestamps.py <input_json> <n_parts> <out_dir>
Writes files: <out_dir>/timestamps_part_0.json ...
"""
import sys
import json
from pathlib import Path

if len(sys.argv) != 4:
    print("Usage: split_timestamps.py <input_json> <n_parts> <out_dir>")
    sys.exit(1)

in_file = Path(sys.argv[1])
n_parts = int(sys.argv[2])
out_dir = Path(sys.argv[3])
out_dir.mkdir(parents=True, exist_ok=True)

data = json.loads(in_file.read_text())
L = len(data)
if L == 0:
    print("[WARN] Empty timestamps list")

base = 0
for i in range(n_parts):
    start = (L * i) // n_parts
    end = (L * (i+1)) // n_parts
    part = data[start:end]
    out_file = out_dir / f"timestamps_part_{i}.json"
    out_file.write_text(json.dumps(part))
    print(f"Wrote {len(part)} timestamps → {out_file}")
