"""
Merge CSV files: event_data.csv + measurements_complete.csv
------------------------------------------------------------
Creates one line per crystal with:
  - image_name
  - x_traj
  - y_traj
  - All crystal characteristics (det_idx, class_id, class_name, confidence, 
    x_center_px, y_center_px, width_px, height_px, longest_px, longest_um, alert)

USAGE:
    python merge_crystals_data.py <run_number>
    or
    python merge_crystals_data.py (uses default run_number = 61)
"""

import sys
import csv
from pathlib import Path
import pandas as pd

# -------------------------
# Argument parsing
# -------------------------
DEFAULT_RUN = 61
run_number = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN

# -------------------------
# Input CSV paths
# -------------------------
results_csv_dir = Path(f"run_{run_number}/results_csv")
results_csv_dir = Path("results_csv")
event_data_csv = results_csv_dir / "event_data.csv"
measurements_csv = results_csv_dir / "measurements_complete.csv"

# Check if files exist
if not event_data_csv.exists():
    raise FileNotFoundError(f"Event data CSV not found: {event_data_csv}")
if not measurements_csv.exists():
    raise FileNotFoundError(f"Measurements CSV not found: {measurements_csv}")

# -------------------------
# Read CSVs
# -------------------------
print(f"Reading event data from: {event_data_csv}")
event_df = pd.read_csv(event_data_csv)

print(f"Reading measurements from: {measurements_csv}")
measurements_df = pd.read_csv(measurements_csv)

# -------------------------
# Merge on image/png_file
# -------------------------
# Rename columns for clarity
event_df.rename(columns={"png_file": "image"}, inplace=True)

# Merge on image column
merged_df = measurements_df.merge(event_df[["image", "xtraj", "ytraj"]], on="image", how="left")

# Reorder columns: image first, then xtraj/ytraj, then all crystal characteristics
column_order = [
    "image",
    "xtraj",
    "ytraj",
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

merged_df = merged_df[column_order]

# -------------------------
# Write merged CSV
# -------------------------
output_csv = results_csv_dir / "merged_crystals.csv"
print(f"\nWriting merged data to: {output_csv}")
merged_df.to_csv(output_csv, index=False)

print(f"✓ Merged {len(merged_df)} crystal detections")
print(f"✓ CSV saved: {output_csv}")
print("\nColumns in merged CSV:")
for i, col in enumerate(column_order, 1):
    print(f"  {i}. {col}")
