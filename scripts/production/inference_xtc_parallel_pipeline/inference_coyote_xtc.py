#!/usr/bin/env python3
"""
YOLOv8 Inference Script → CSV (sizes) + above-threshold CSV
------------------------------------------------------------
- Runs YOLO inference on a folder of images
- Computes longest side per detection in px and μm
- Flags detections larger than a given μm threshold
- Writes:
    1) results_csv/measurements_complete.csv  (ALL detections)
    2) results_csv/measurements_above_threshold.csv (ONLY detections above threshold)

USAGE:
    python inference_coyote_xtc.py <chip_pic_dir>
"""

import os
import sys
import csv
from pathlib import Path
import numpy as np
from ultralytics import YOLO

# -------------------------
# Argument parsing
# -------------------------
if len(sys.argv) != 2:
    print("Usage: python inference_coyote_xtc.py <chip_pic_dir>")
    sys.exit(1)

chip_pic_dir = sys.argv[1]
if not os.path.isdir(chip_pic_dir):
    raise ValueError(f"Provided chip_pic_dir does not exist: {chip_pic_dir}")

# -------------------------
# Paths / parameters
# -------------------------
weights_path = (
    "/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote/latest_weights/weights_yolov11n_150epochs_merged_dataset.pt"
)

mag_factor = 5.56     # optical magnification
px_size = 3.45        # pixel size (μm)
downsamp_factor = 2    # if images were downsampled before inference
px_to_um = px_size * downsamp_factor / mag_factor
alert_um = 5.0       # threshold, in μm, above which to flag detections, set very low for development/testing purpose

# Output CSV directory
out_dir = Path("results_csv")
out_dir.mkdir(parents=True, exist_ok=True)

csv_all_tmp = out_dir / "measurements.csv"
csv_all_final = out_dir / "measurements_complete.csv"
csv_above = out_dir / "measurements_above_threshold.csv"

# -------------------------
# Load model
# -------------------------
model = YOLO(weights_path)

# -------------------------
# Run prediction
# -------------------------
results = model.predict(
    source=chip_pic_dir,
    save=True,
    verbose=True
)

# -------------------------
# CSV header
# -------------------------
header = [
    "image",
    "det_idx",
    "class_id",
    "class_name",
    "confidence",
    "x_center_px",
    "y_center_px",
    "width_px",
    "height_px",
    "longest_px",
    "longest_um",
    "alert"
]

# -------------------------
# Write BOTH CSVs
# -------------------------
with open(csv_all_tmp, "w", newline="") as f_all, open(csv_above, "w", newline="") as f_above:
    w_all = csv.writer(f_all)
    w_above = csv.writer(f_above)

    w_all.writerow(header)
    w_above.writerow(header)

    for r in results:
        img_name = os.path.basename(r.path)

        if r.boxes is None or len(r.boxes) == 0:
            continue

        xywh = r.boxes.xywh.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy() if r.boxes.conf is not None else np.array([])
        clses = r.boxes.cls.cpu().numpy().astype(int) if r.boxes.cls is not None else np.array([], dtype=int)

        for i, (x_c, y_c, bw, bh) in enumerate(xywh):
            longest_px = float(max(bw, bh))
            longest_um = longest_px * px_to_um

            cls_id = int(clses[i]) if clses.size > i else -1
            cls_name = model.names.get(cls_id, str(cls_id))
            conf = float(confs[i]) if confs.size > i else float("nan")

            is_above = longest_um > alert_um
            alert_flag = "STOP" if is_above else ""

            if is_above:
                print(
                    f"[STOP] {img_name} — det {i+1}: "
                    f"{longest_um:.2f} μm > {alert_um} μm → Stop the beam"
                )

            row = [
                img_name,
                i + 1,
                cls_id,
                cls_name,
                f"{conf:.4f}",
                f"{x_c:.2f}",
                f"{y_c:.2f}",
                f"{bw:.2f}",
                f"{bh:.2f}",
                f"{longest_px:.2f}",
                f"{longest_um:.2f}",
                alert_flag
            ]

            # Write to "all detections"
            w_all.writerow(row)

            # Write to "above threshold only"
            if is_above:
                w_above.writerow(row)

print(f"\nCSV (all) saved to: {csv_all_tmp}")
print(f"CSV (above threshold only) saved to: {csv_above}")

# Rename "all" CSV after completion
if csv_all_final.exists():
    csv_all_final.unlink()
csv_all_tmp.rename(csv_all_final)

print(f"CSV (all) renamed to: {csv_all_final}")
