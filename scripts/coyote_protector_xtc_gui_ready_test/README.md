## COYOTE PROTECTOR XTC GUI READY

This folder contains a complete workflow for processing XTC data from LCLS experiments, extracting images, running YOLO-based crystal detection, and generating comprehensive CSV reports with trajectory information.

## Key Highlights:
- Export raw XTC detector data to PNG images with normalized versions
- Fine-tuned YOLOv11 model for accurate crystal detection
- Pixel-to-micron size conversion and threshold alert system
- CSV merging to combine trajectory and crystal detection data
- Organized results in `results_csv/` folder within run directories

## Overview of the Scripts

This workflow consists of two main processing stages:

### Stage 1: XTC Data Export
**Script:** `export_xtc_normalized_args.py`
- Extracts images from LCLS XTC files using psana
- Saves raw and normalized (contrast-enhanced) PNG images
- Records trajectory coordinates (XTRAJ, YTRAJ) for each event
- Outputs: `run_{run_number}_png/`, `run_{run_number}_png_norm/`, `event_data.csv`

### Stage 2: Crystal Detection (YOLO Inference)
**Script:** `inference_coyote_xtc.py`
- Runs YOLOv11 inference on exported PNG images
- Detects crystals and computes size in pixels and microns
- Generates two CSV files:
  - `measurements_complete.csv` - All detections
  - `measurements_above_threshold_complete.csv` - Only detections exceeding size threshold
- Outputs: Both CSVs in `results_csv/` folder

### Stage 3: Data Merging
**Script:** `merge_crystals_data.py`
- Merges event trajectory data with crystal detection results
- Creates one line per crystal with all relevant information
- Output: `merged_crystals.csv` in `results_csv/` folder with columns: image, xtraj, ytraj, and all crystal characteristics

### Orchestration Script
**Script:** `run_export_infer_xtc.sh`
- Bash wrapper that runs both export and inference scripts sequentially
- Simplifies execution of the complete workflow

## Setting up the Coyote Protector XTC Workflow

### 1. Prerequisites
- psana environment (for XTC data access): `source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh`
- YOLO weights file (`.pt` model)
- LCLS experiment identifier and run number

### 2. Configure `inference_coyote_xtc.py`
Edit the script to set detection parameters:
```python
weights_path = "/path/to/your/weights/best.pt"  # Path to YOLO model weights
mag_factor = 5.56                                # Optical magnification
px_size = 3.45                                   # Pixel size in microns
dowsamp_factor = 2                               # Downsampling factor (if applied)
px_to_um = px_size * dowsamp_factor / mag_factor # Computed pixel-to-micron conversion
alert_um = 50.0                                  # Size threshold in microns
```

**Output Structure:**
```
results_csv/
├── measurements_complete.csv                    # All detections
└── measurements_above_threshold_complete.csv    # Detections > alert_um threshold
```

### 4. Configure `merge_crystals_data.py`
No configuration needed — it automatically reads from the results_csv folder and merges the data.


## Running the Complete Workflow

### Using sbatch with Environment Variables 

The scripts are designed to be submitted via SLURM's `sbatch` command with environment variables passed as key=value pairs.

#### Syntax:
```bash
sbatch <script.sh> RUN_NUMBER=<value> EXP_NUMBER=<value> MAX_EVENTS=<value>
```

**Parameter Descriptions:**
- `RUN_NUMBER`: LCLS run number to process (e.g., 61)
- `EXP_NUMBER`: Experiment identifier (e.g., mfx101346325, xpp)
- `MAX_EVENTS`: Maximum number of events to process (e.g., 80000)

#### Examples:

**Complete Workflow (Export + Inference):**
```bash
sbatch run_export_infer_xtc.sh RUN_NUMBER=61 EXP_NUMBER=mfx101346325 MAX_EVENTS=80000
```

**Export Only:**
Parameters have to be changed into the script directly (no parsing)
```bash
sbatch run_export_xtc.sh
```

**Inference Only:**
Parameters have to be changed into the script directly (no parsing)
```bash
sbatch run_inference_xtc.sh RUN_NUMBER=61
```

**Check Job Status:**
```bash
# View all your jobs
squeue -u $(whoami)

# View specific job details
squeue -j <job_id>

# Check job logs
tail -f logs_export/export_turing_<job_id>.out
```

### Running Scripts Interactively (Alternative)

If you prefer not to use sbatch or need to run interactively:

**Step 1: Export XTC Data**
```bash
# Must source psana environment first!
source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh

python export_xtc_normalized_args.py <run_number> <exp_number> <save_normalized> <max_events>

# Example:
python export_xtc_normalized_args.py 61 mfx101346325 1 80000
```

**Step 2: Run Crystal Detection**
```bash
python inference_coyote_xtc.py <chip_pic_dir>

# Example (using normalized images):
python inference_coyote_xtc.py run_61/run_61_png_norm
```

**Step 3: Merge Results**
```bash
python merge_crystals_data.py <run_number>

# Example:
python merge_crystals_data.py 61
```

## Output Files Description

### From `export_xtc_normalized_args.py`
- `run_{run_number}/results_csv/event_data.csv`
  - Columns: `event_id, png_file, xtraj, ytraj`
  - One row per event/frame processed

### From `inference_coyote_xtc.py`
- `results_csv/measurements_complete.csv`
  - Columns: `image, det_idx, class_id, class_name, confidence, x_center_px, y_center_px, width_px, height_px, longest_px, longest_um, alert`
  - All detected crystals

- `results_csv/measurements_above_threshold_complete.csv`
  - Same columns as above
  - Only crystals with `longest_um > alert_um`

### From `merge_crystals_data.py`
- `run_{run_number}/results_csv/merged_crystals.csv`
  - Columns: `image, xtraj, ytraj, det_idx, class_id, class_name, confidence, x_center_px, y_center_px, width_px, height_px, longest_px, longest_um, alert`
  - One row per crystal detection
  - Includes trajectory coordinates matched by image name

## Typical Workflow Example

```bash
# Example: Process run 61 with 80,000 events
sbatch run_export_infer_xtc.sh RUN_NUMBER=61 EXP_NUMBER=mfx101346325MAX_EVENTS=80000

# Monitor job status
squeue -u $(whoami)

# Check output (once job is running or complete)
tail -f logs_export/export_turing_<job_id>.out

# Once complete, verify results
ls -lh run_61/results_csv/
# Should contain:
#   event_data.csv
#   measurements_complete.csv
#   measurements_above_threshold_complete.csv
#   merged_crystals.csv
```

## Result Summary

After running the complete workflow, you will have:

1. **Extracted Images:** Raw and normalized PNG files from XTC detector data
2. **Event Data:** CSV with trajectory coordinates for each event
3. **Crystal Detections:** Two CSVs with detection results (all and filtered by size threshold)
4. **Merged Dataset:** Single comprehensive CSV combining all information, ready for analysis

All results are organized in the `run_{run_number}/results_csv/` directory for easy access and further analysis.

## Troubleshooting

### psana import error
Make sure to source the psana environment before running export script:
```bash
source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh
```

### YOLO weights not found
Verify the path in `inference_coyote_xtc.py`:
```python
weights_path = "/path/to/your/weights.pt"
```

### No images detected during inference
- Check that images were successfully saved in `run_{run_number}_png/` or `run_{run_number}_png_norm/`
- Verify the image directory path passed to inference script is correct
- Check image file format (should be `.png`)

### CSV merge fails
- Ensure both `event_data.csv` and `measurements_complete.csv` exist in `run_{run_number}/results_csv/`
- Verify image filenames match between the two CSVs (event filenames should match YOLO output filenames)
