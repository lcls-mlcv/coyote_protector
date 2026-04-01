# NOT RECOMMANDED : OBSOLETE VERSION KEPT ONLY FOR LEGACY PURPOSE

# Coyote Protector Serial Workflow

This folder contains the end-to-end serial workflow used to process LCLS runs, export detector PNGs, run YOLO inference, and merge trajectory + crystal detection results into final CSV files.

The general workflow is the following:
- a script is launched from CDS to launch processing on SDF
- images and metadata are processed on SDF
- relevant CSV outputs can be copied back to CDS

Unlike the parallel pipeline, this version does not split timestamps into chunks and does not submit worker jobs per part.

## Quick setup on SDF and sync to CDS

1) Create a folder on SDF in your experiment results area.

This folder hosts the code and output of processing (images, logs, and CSV files).

- SSH to psana and run:
```bash
mkdir -p "/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/"
```

2) Clone the full repo, then navigate to the serial production folder:

```bash
git clone git@github.com:lcls-mlcv/coyote_protector.git
cd /sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_serial_pipeline/
```

3) If launching from CDS, update `routine_detection_v3.sh` before syncing:

- `DEST_HOST="psana.sdf.slac.stanford.edu"`
- `SDF_BASE` should point to something similar to `/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_serial_pipeline/`
- `RESULTS_BACK_BASE` should point to your CDS destination folder

These are user-specific and should be changed for production.

4) Rsync that SDF folder to CDS (optional, if orchestrating from CDS):

```bash
rsync -av "${USER_NAME}@${DEST_HOST}:/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_serial_pipeline/" ./
```

5) (Optional) Passwordless SSH setup (CDS -> SDF)

Some steps in this pipeline connect multiple times to SDF (`psana.sdf.slac.stanford.edu`) using `ssh`.
If SSH keys are not configured, you will be prompted for your password repeatedly.

To avoid repeated authentication, configure passwordless SSH from CDS to SDF before production runs.

- Generate an SSH key on CDS:

```bash
ssh-keygen -t ed25519
```

- Authorize the public key on SDF:

```bash
ssh-copy-id <username>@psana.sdf.slac.stanford.edu
```

- Test from CDS:

```bash
ssh <username>@psana.sdf.slac.stanford.edu
```

6) Run from CDS:

```bash
source /cds/group/pcds/pyps/conda/pcds_conda
python bash_launcher.py --user=<username> --run_number=<run_number> --exp_number=<experiment_id> --max_events=<max_events> --camera_name=<camera_name> > quick_run.log &
```

## Required configuration before production

Review these hardcoded values before production runs.

### 1) SLURM resources/accounts

- `run_export_infer_xtc.sh`
  - `#SBATCH --account=lcls:prjlumine22`
  - `#SBATCH --partition=turing`
  - `#SBATCH --gpus=1`

- `run_export_xtc.sh`
  - `#SBATCH --account=lcls:prjlumine22`
  - `#SBATCH --partition=turing`

- `run_inference_xtc.sh`
  - `#SBATCH --account=lcls:prjlumine22`
  - `#SBATCH --partition=turing`
  - `#SBATCH --gpus=1`

You must have access to these resources and projects.

### 2) Python environments

- psana env sourced by export scripts:
  - `/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh`

- YOLO Python binary used by inference/merge:
  - `YOLO_PYTHON=/sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/bin/python`

Note : you must have the access to prjlumine22 to use this environment, will be build in lcls-tools soon.

### 3) YOLO model + calibration

In `inference_coyote_xtc.py` on SDF, verify:
- `weights_path`
- `mag_factor`      # magnification factor from the microscope
- `px_size`         # real pixel size (in micro meters)
- `downsamp_factor` # camera downsampling factor (usually 2)
- `alert_um`        # threshold above which the crystal is considerd to be dangerous for the dector (set artifically low for development purpose)

Note : the last 4 values are is setup dependant, please use the operators for the values.

### 4) Orchestrator paths (CDS ↔ SDF)

In `routine_detection_v3.sh`, verify:
- `SDF_BASE`
- `RESULTS_BACK_BASE`
- `DEST_HOST`

## Run options

## A) Launch from CDS with Python wrapper

```bash
python bash_launcher.py \
  --user=<username> \
  --run_number=61 \
  --exp_number=mfx101346325 \
  --save_normalized=1 \
  --max_events=80000 \
  --use_normalized=1 \
  --camera_name=inline_alvium
```

Dry-run (prints command only):

```bash
python bash_launcher.py --dry_run
```

This calls `routine_detection_v3.sh`, which submits `run_export_infer_xtc.sh` on SDF and copies back `run_<run>/results_csv/`.

## B) Recommended: full serial workflow on SDF

```bash
sbatch run_export_infer_xtc.sh \
  RUN_NUMBER=61 \
  EXP_NUMBER=mfx101346325 \
  SAVE_NORMALIZED=1 \
  MAX_EVENTS=80000 \
  USE_NORMALIZED=1 \
  CAMERA_NAME=inline_alvium
```

What it does:
- creates `run_<RUN_NUMBER>/`
- `cd` into `run_<RUN_NUMBER>/`
- exports images + `results_csv/event_data.csv`
- runs inference and writes `results_csv/measurements_*.csv`
- merges to `results_csv/merged_crystals.csv`

## C) Export only

```bash
sbatch run_export_xtc.sh \
  RUN_NUMBER=61 \
  EXP_NUMBER=mfx101346325 \
  SAVE_NORMALIZED=1 \
  MAX_EVENTS=80000 \
  CAMERA_NAME=inline_alvium
```

Note: this script does not create `run_<RUN_NUMBER>/` before export. It writes image folders (`run_<RUN_NUMBER>_png*`) and `results_csv/event_data.csv` relative to the directory where the job runs.

## D) Inference + merge only (after export)

```bash
sbatch run_inference_xtc.sh RUN_NUMBER=61 USE_NORMALIZED=1
```

Important behavior:
- `run_inference_xtc.sh` expects images under `run_<RUN_NUMBER>/run_<RUN_NUMBER>_png_norm` (or `_png`)
- `inference_coyote_xtc.py` and `merge_crystals_data.py` write/read `results_csv` in the current working directory

So this script is only safe if your current directory and exported image layout are consistent with those assumptions.


## Monitoring and logs

Check jobs:

```bash
squeue -u $(whoami)
```

Master sequential logs:

```bash
tail -f logs_export/export_infer_turing_<jobid>.out
tail -f logs_export/export_infer_turing_<jobid>.err
```

Export-only logs:

```bash
tail -f logs_export/export_turing_<jobid>.out
tail -f logs_export/export_turing_<jobid>.err
```

Inference-only logs:

```bash
tail -f logs_export/inference_turing_<jobid>.out
tail -f logs_export/inference_turing_<jobid>.err
```

## Output layout

### Full sequential run (`run_export_infer_xtc.sh`)

Inside `run_<RUN_NUMBER>/`:

- `run_<RUN_NUMBER>_png/` (raw write currently disabled in export script)
- `run_<RUN_NUMBER>_png_norm/` (when `SAVE_NORMALIZED=1`)
- `results_csv/`
  - `event_data.csv`
  - `measurements_complete.csv`
  - `measurements_above_threshold.csv`
  - `merged_crystals.csv`

### Orchestrated run from CDS (`routine_detection_v3.sh`)

On CDS destination:
- `run_<RUN_NUMBER>_results/`
  - synchronized copy of SDF `run_<RUN_NUMBER>/results_csv/`

## Common issues

- `psana` import fails
  Source psana env before export scripts:
  ```bash
  source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh
  ```

- YOLO inference fails to start
  Validate `YOLO_PYTHON` in shell scripts and `weights_path` in `inference_coyote_xtc.py`.

- Missing images
  `export_xtc_normalized_args.py` processes one event every 3 events (`eid % 3 == 0`). Also, raw PNG write is commented out, so typically only normalized images are written.

- Merge file-not-found
  `merge_crystals_data.py` reads from `results_csv/event_data.csv` and `results_csv/measurements_above_threshold.csv` in the current working directory.

- Routine output lists a wrong file name
  `routine_detection_v3.sh` prints `measurements_above_threshold_complete.csv`, but inference writes `measurements_above_threshold.csv`.

## Minimal reproducible command

```bash
sbatch run_export_infer_xtc.sh RUN_NUMBER=61 EXP_NUMBER=mfx101346325 SAVE_NORMALIZED=1 MAX_EVENTS=100 USE_NORMALIZED=1 CAMERA_NAME=inline_alvium
```

When complete:

```bash
ls -lh run_61/results_csv/
```

## What this pipeline does in detail

1. Export XTC detector frames and trajectory metadata (`export_xtc_normalized_args.py`)
2. Run YOLO on exported image folder (`inference_coyote_xtc.py`)
3. Merge detections with XTRAJ/YTRAJ by image filename (`merge_crystals_data.py`)
4. Optional CDS orchestrator submits on SDF and pulls CSVs back (`routine_detection_v3.sh`)

## Folder scripts

- `bash_launcher.py`
  Python launcher for `routine_detection_v3.sh` with CLI args.

- `routine_detection_v3.sh`
  Runs from CDS, SSHs to SDF, submits sequential SLURM job, waits for merged CSV, and rsyncs results back.

- `run_export_infer_xtc.sh`
  Single sequential SLURM job: export -> inference -> merge, inside `run_<RUN_NUMBER>/`.

- `run_export_xtc.sh`
  Export-only SLURM job.

- `run_inference_xtc.sh`
  Inference + merge SLURM job.

- `export_xtc_normalized_args.py`
  Exports normalized PNGs and `event_data.csv` from XTC.

- `inference_coyote_xtc.py`
  Runs YOLO and writes `measurements_complete.csv` and `measurements_above_threshold.csv`.

- `merge_crystals_data.py`
  Merges trajectory data and above-threshold detections into `merged_crystals.csv`.

## CSV schema summary

### `event_data.csv`

Columns:
- `event_id`
- `png_file`
- `xtraj`
- `ytraj`

### `measurements_complete.csv` and `measurements_above_threshold.csv`

Columns:
- `image`
- `det_idx`
- `class_id`
- `class_name`
- `confidence`
- `x_center_px`
- `y_center_px`
- `width_px`
- `height_px`
- `longest_px`
- `longest_um`
- `alert`

### `merged_crystals.csv`

Columns:
- `image`
- `xtraj`
- `ytraj`
- `det_idx`
- `class_id`
- `class_name`
- `confidence`
- `x_center_px`
- `y_center_px`
- `width_px`
- `height_px`
- `longest_px`
- `longest_um`
- `alert`

Note: current merge uses `measurements_above_threshold.csv` (not all detections).

## Precise inputs/outputs by algorithm (reference)

This section is the contract for each script: exact runtime inputs, what it reads, and what it writes.

### 1) `export_xtc_normalized_args.py`

CLI input:

```bash
python export_xtc_normalized_args.py [run_number] [exp_number] [save_normalized] [max_events] [camera_name]
```

Defaults in script:
- `run_number=61`
- `exp="mfx  "` (must usually be overridden)
- `save_normalized=True`
- `max_events=10000`
- `camera_name="inline_alvium"`

Reads:
- psana datasource from `exp/run/max_events`
- detectors: `<camera_name>`, `XTRAJ`, `YTRAJ`

Writes:
- `run_<run>_png/event_<event_id>.png` (raw write currently commented out)
- `run_<run>_png_norm/event_<event_id>.png` (if `save_normalized` true)
- `results_csv/event_data.csv`

Specific behavior:
- processes only events where `event_id % 3 == 0`
- stores CSV `png_file` as raw filename pattern `event_<event_id>.png`

### 2) `inference_coyote_xtc.py`

CLI input:

```bash
python inference_coyote_xtc.py <chip_pic_dir>
```

Reads:
- image files from `<chip_pic_dir>`
- YOLO weights from hardcoded `weights_path`

Writes:
- `results_csv/measurements_complete.csv`
- `results_csv/measurements_above_threshold.csv`

Thresholding behavior:
- computes `longest_um = max(width_px, height_px) * px_to_um`
- flags row with `alert="STOP"` when `longest_um > alert_um`
- writes all rows to `measurements_complete.csv` and only flagged rows to `measurements_above_threshold.csv`

### 3) `merge_crystals_data.py`

CLI input:

```bash
python merge_crystals_data.py [run_number]
```

Reads:
- `results_csv/event_data.csv`
- `results_csv/measurements_above_threshold.csv`

Writes:
- `results_csv/merged_crystals.csv`

Merge logic:
- renames `event_data.csv` column `png_file` -> `image`
- left-merges measurements with `xtraj,ytraj` on `image`

### 4) `run_export_infer_xtc.sh`

Runtime key=value inputs:
- `RUN_NUMBER`
- `EXP_NUMBER`
- `SAVE_NORMALIZED`
- `MAX_EVENTS`
- `USE_NORMALIZED`
- `CAMERA_NAME`

Behavior:
- creates and enters `run_<RUN_NUMBER>/`
- runs export (`../export_xtc_normalized_args.py`)
- runs inference (`../inference_coyote_xtc.py`)
- runs merge (`../merge_crystals_data.py`)

Writes inside `run_<RUN_NUMBER>/`:
- `run_<RUN_NUMBER>_png/`
- `run_<RUN_NUMBER>_png_norm/`
- `results_csv/event_data.csv`
- `results_csv/measurements_complete.csv`
- `results_csv/measurements_above_threshold.csv`
- `results_csv/merged_crystals.csv`

### 5) `run_export_xtc.sh`

Runtime key=value inputs:
- `RUN_NUMBER`
- `EXP_NUMBER`
- `SAVE_NORMALIZED`
- `MAX_EVENTS`
- `CAMERA_NAME`

Behavior:
- runs `./export_xtc_normalized_args.py` in current folder (no automatic `run_<RUN_NUMBER>/` `cd`)

Writes in current folder:
- `run_<RUN_NUMBER>_png/`
- `run_<RUN_NUMBER>_png_norm/`
- `results_csv/event_data.csv`

### 6) `run_inference_xtc.sh`

Runtime key=value inputs:
- `RUN_NUMBER`
- `USE_NORMALIZED`

Reads image folder:
- `run_<RUN_NUMBER>/run_<RUN_NUMBER>_png_norm` or `run_<RUN_NUMBER>/run_<RUN_NUMBER>_png`

Runs:
- `./inference_coyote_xtc.py <image_dir>`
- `./merge_crystals_data.py <run_number>`

Writes in current folder:
- `results_csv/measurements_complete.csv`
- `results_csv/measurements_above_threshold.csv`
- `results_csv/merged_crystals.csv`
