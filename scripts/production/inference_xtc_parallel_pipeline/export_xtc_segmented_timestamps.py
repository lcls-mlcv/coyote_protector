# Must source this env before running:
# source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh

import sys
import json
import csv
import numpy as np
import cv2
from pathlib import Path
from psana import DataSource

# -------------------------
# Argument parsing
# -------------------------
DEFAULT_RUN = 146
DEFAULT_EXP = "mfx101232725"
DEFAULT_MAX_EVENTS = 100
DEFAULT_TIMESTAMPS = None
DEFAULT_ORIGINAL_TIMESTAMPS = None

argc = len(sys.argv)

if argc == 1:
    run_number = DEFAULT_RUN
    exp = DEFAULT_EXP
    max_events = DEFAULT_MAX_EVENTS
    timestamps_json = DEFAULT_TIMESTAMPS
    original_timestamps_json = DEFAULT_ORIGINAL_TIMESTAMPS
elif argc in (2, 3, 4, 5, 6):
    run_number = int(sys.argv[1])
    exp = sys.argv[2] if argc >= 3 else DEFAULT_EXP
    max_events = int(sys.argv[3]) if argc >= 4 else DEFAULT_MAX_EVENTS
    timestamps_json = sys.argv[4] if argc >= 5 else DEFAULT_TIMESTAMPS
    original_timestamps_json = sys.argv[5] if argc >= 6 else DEFAULT_ORIGINAL_TIMESTAMPS
else:
    print(
        "Usage:\n"
        "  python export_xtc_segmented_timestamps.py\n"
        "  python export_xtc_segmented_timestamps.py <run_number>\n"
        "  python export_xtc_segmented_timestamps.py <run_number> <exp_number>\n"
        "  python export_xtc_segmented_timestamps.py <run_number> <exp_number> <max_events>\n"
        "  python export_xtc_segmented_timestamps.py <run_number> <exp_number> <max_events> <timestamps_json>\n"
        "  python export_xtc_segmented_timestamps.py <run_number> <exp_number> <max_events> <timestamps_json> <original_timestamps_json>\n"
    )
    sys.exit(1)

print(f"[CONFIG] exp={exp} run={run_number} max_events={max_events} timestamps_json={timestamps_json} original_timestamps_json={original_timestamps_json}")

# -------------------------
# Load timestamps from JSON
# -------------------------
# Load original timestamps mapping (for consistent event_id across all parts)
original_ts_to_idx = None
if original_timestamps_json and Path(original_timestamps_json).exists():
    with open(original_timestamps_json, "r") as f:
        original_timestamps_list = json.load(f)
    original_ts_to_idx = {int(ts): i for i, ts in enumerate(original_timestamps_list)}
    print(f"[INFO] Loaded {len(original_timestamps_list)} original timestamps for ID mapping → {original_timestamps_json}")

# Load partial timestamps for this part (or all if not specified)
if timestamps_json and Path(timestamps_json).exists():
    with open(timestamps_json, "r") as f:
        timestamps_list = json.load(f)
    timestamps_array = np.array(timestamps_list, dtype=np.uint64)
    print(f"[INFO] Loaded {len(timestamps_list)} partial timestamps for processing → {timestamps_json}")
else:
    timestamps_array = None
    if timestamps_json:
        print(f"[WARNING] Timestamps file {timestamps_json} not found - processing all events")

# -------------------------
# psana setup
# -------------------------
if timestamps_array is not None:
    ds = DataSource(exp=exp, run=[run_number], max_events=max_events, timestamps=timestamps_array)
else:
    ds = DataSource(exp=exp, run=[run_number], max_events=max_events)

myrun = next(ds.runs())

# Get detectors
cam = myrun.Detector("inline_alvium")
xtraj = myrun.Detector("XTRAJ")
ytraj = myrun.Detector("YTRAJ")

# -------------------------
# Output dirs and CSV
# -------------------------
out_dir = Path(f"run_{run_number}_png")
out_dir.mkdir(exist_ok=True)

norm_dir = Path(f"run_{run_number}_png_norm")
norm_dir.mkdir(exist_ok=True)

csv_path = out_dir / "event_data.csv"
csv_file = open(csv_path, "w", newline="")
writer = csv.writer(csv_file)
writer.writerow(["event_id", "timestamp", "png_file", "xtraj", "ytraj"])

# -------------------------
# Event loop
# -------------------------
event_count = 0

for evt in myrun.events():
    ts = int(evt.timestamp)
    
    # Get the event_id from original timestamps mapping (if available), else use counter
    if original_ts_to_idx is not None:
        eid = original_ts_to_idx.get(ts)
        if eid is None:
            print(f"[WARNING] Timestamp {ts} not found in original mapping, skipping")
            continue
    else:
        eid = event_count
    
    # Get image
    img = cam.raw.value(evt)
    if img is None:
        print(f"[WARNING] Image is None for event_id={eid}, skipping")
        continue
    
    # Get trajectory data
    x = xtraj(evt)
    y = ytraj(evt)
    
    # Extract x and y values for this event using the index
    x_val = x[eid] if x is not None and eid < len(x) else None
    y_val = y[eid] if y is not None and eid < len(y) else None
    
    # Normalize image
    img8 = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    fname_norm = norm_dir / f"event_{eid:06d}.png"
    cv2.imwrite(str(fname_norm), img8)
    
    # CSV entry
    writer.writerow([eid, ts, fname_norm.name, x_val, y_val])
    print(f"[EVENT {eid}] timestamp={ts} png={fname_norm.name} xtraj={x_val} ytraj={y_val}", end="\r")
    
    event_count += 1

csv_file.close()

print(f"\n[INFO] Processed {event_count} events")
print(f"[INFO] Saved normalized PNG images → {norm_dir}")
print(f"[INFO] CSV saved → {csv_path}")
