
## same as test_xtc/inference_coyote.py but with argument parsing
"""
YOLOv8 Inference Script → CSV (sizes)
------------------------------------------------------------
- Runs YOLO inference on a folder of images
- Computes longest side per detection in px and μm
- Flags detections larger than a given μm threshold

USAGE:
    python inference_coyote_xtc.py <chip_pic_dir>

EDIT THESE BEFORE RUNNING:
 - weights_path: Path to your trained YOLO weights (.pt)
 - px_to_um:     Pixel-to-micron conversion factor for your setup
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
    "/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/scripts/runs/detect/train_150epochs_v11_merged/weights/best.pt"
)

'''
weights_path = (
    "/sdf/home/p/pmonteil/prjlumine22/results/pmonteil/"
    "coyote_beamtime_19jan/weight_yolov11n_150epochs.pt"
)
'''

mag_factor = 5.56     # optical magnification
px_size = 3.45        # pixel size (μm)
dowsamp_factor = 2  # if images were downsampled before inference
px_to_um = px_size*dowsamp_factor / mag_factor
alert_um = 50.0 #threshold, in μm, above which to flag detections

# Output CSV directory
#out_dir = Path("runs/size_measurements")
out_dir = Path("results_csv")
out_dir.mkdir(parents=True, exist_ok=True)
csv_path = out_dir / "measurements.csv"

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
# Write CSV
# -------------------------
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
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
    ])

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

            alert_flag = "STOP" if longest_um > alert_um else ""
            if alert_flag:
                print(
                    f"[STOP] {img_name} — det {i+1}: "
                    f"{longest_um:.2f} μm > {alert_um} μm → Stop the beam"
                )

            writer.writerow([
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
            ])

print(f"\nCSV saved to: {csv_path}")

# Rename CSV after completion
final_csv_path = out_dir / "measurements_complete.csv"
csv_path.rename(final_csv_path)

print(f"CSV renamed to: {final_csv_path}")
