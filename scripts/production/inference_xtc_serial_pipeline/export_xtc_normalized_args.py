# Must source this env before running:
# source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh

import os
import sys
import csv
from pathlib import Path
import cv2
import numpy as np
from psana import DataSource


def parse_bool(s: str) -> bool:
    """Accept 1/0, true/false, yes/no (case-insensitive)."""
    v = s.strip().lower()
    if v in ("1", "true", "t", "yes", "y", "on"):
        return True
    if v in ("0", "false", "f", "no", "n", "off"):
        return False
    raise ValueError(f"Could not parse boolean from: {s!r}")


# -------------------------
# Argument parsing
# -------------------------
DEFAULT_RUN = 61
DEFAULT_EXP = "mfx  "
DEFAULT_SAVE_NORM = True
DEFAULT_MAX_EVENTS = 10000
DEFAULT_CAMERA = "inline_alvium"

argc = len(sys.argv)

if argc == 1:
    run_number = DEFAULT_RUN
    exp = DEFAULT_EXP
    SAVE_NORMALIZED = DEFAULT_SAVE_NORM
    max_events = DEFAULT_MAX_EVENTS
    camera_name = DEFAULT_CAMERA
elif argc in (2, 3, 4, 5, 6):
    run_number = int(sys.argv[1])
    exp = sys.argv[2] if argc >= 3 else DEFAULT_EXP
    SAVE_NORMALIZED = parse_bool(sys.argv[3]) if argc >= 4 else DEFAULT_SAVE_NORM
    max_events = int(sys.argv[4]) if argc >= 5 else DEFAULT_MAX_EVENTS
    camera_name = sys.argv[5] if argc >= 6 else DEFAULT_CAMERA
else:
    print(
        "Usage:\n"
        "  python export_xtc_normalized.py\n"
        "  python export_xtc_normalized.py <run_number>\n"
        "  python export_xtc_normalized.py <run_number> <exp_number>\n"
        "  python export_xtc_normalized.py <run_number> <exp_number> <save_normalized>\n"
        "  python export_xtc_normalized.py <run_number> <exp_number> <save_normalized> <max_events>\n"
        "  python export_xtc_normalized.py <run_number> <exp_number> <save_normalized> <max_events> <camera_name>\n"
    )
    sys.exit(1)

print(f"[CONFIG] exp={exp} run={run_number} save_normalized={SAVE_NORMALIZED} max_events={max_events} camera_name={camera_name}")

# -------------------------
# psana setup
# -------------------------
#print(run_number, exp, max_events, SAVE_NORMALIZED)
ds = DataSource(exp=exp, run=[run_number], max_events=max_events)

myrun = next(ds.runs())

cam = myrun.Detector(camera_name)
xtraj = myrun.Detector("XTRAJ")
ytraj = myrun.Detector("YTRAJ")

# -------------------------
# Output dirs
# -------------------------
out_dir = Path(f"run_{run_number}_png")
out_dir.mkdir(exist_ok=True)

norm_dir = Path(f"run_{run_number}_png_norm")
if SAVE_NORMALIZED:
    norm_dir.mkdir(exist_ok=True)

# -------------------------
# CSV (manual open/close — SAME as second script)
# -------------------------
out_dir_csv = Path("results_csv")
out_dir_csv.mkdir(exist_ok=True)
csv_path = out_dir_csv / "event_data.csv"
csv_file = open(csv_path, "w", newline="")
writer = csv.writer(csv_file)
writer.writerow(["event_id", "png_file", "xtraj", "ytraj"])

# -------------------------
# Event loop
# -------------------------
eid = 0

for evt in myrun.events():
    if eid % 3 == 0 :
        img = cam.raw.value(evt)
        if img is None:
            eid += 1
            continue

        x = xtraj(evt)
        y = ytraj(evt)

        # Save raw
        fname = out_dir / f"event_{eid:06d}.png"
        #cv2.imwrite(str(fname), img)

        # Save normalized
        if SAVE_NORMALIZED:
            img8 = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            fname_norm = norm_dir / f"event_{eid:06d}.png"
            cv2.imwrite(str(fname_norm), img8)

        # CSV entry (same as your second script)
        writer.writerow([eid, fname.name, x[eid], y[eid]])

        print(f"[EVENT {eid}] Saved {fname.name} | X={x[eid]}, Y={y[eid]}")

    eid += 1

csv_file.close()

print(f"\n[INFO] Saved {eid} raw images → {out_dir}")
if SAVE_NORMALIZED:
    print(f"[INFO] Saved {eid} normalized images → {norm_dir}")
print(f"[INFO] CSV saved → {csv_path}")
