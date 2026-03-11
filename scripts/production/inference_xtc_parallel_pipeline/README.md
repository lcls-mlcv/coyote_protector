# Coyote Protector Parallelized Workflow

This folder contains the end-to-end workflow used to process LCLS runs, export normalized detector PNGs, run YOLO inference in parallel chunks, and merge trajectory + crystal detection results into final CSV files.

The general workflow is the following:
- a script is launched from CDS to launch processing on SDF.
- images and metadata are processed and stored on SDF
- relevant data (crystal positions) is sent back to CDS as CSV files in a specified folder

This requires loading code on both SDF and CDS and updating a few configuration values. The process is described below.

## Quick setup on SDF and sync to CDS

1) Create a folder on SDF in your experiment results area.

This folder will host the code to process the data (xtc export, slice and post-process with YOLO) and the output of the processing (annotated images and .csv) will be stored there.

- SSH to psana and run:
```bash
mkdir -p \"/sdf/data/lcls/ds/mfx/exp_id/results/your/folder/to/process/images" #change exp_id to something relevant (e.g mfx101232725)
```
Note: it is recommended to use a folder with significant storage, like the experiment folder, in case you want to store annotated images.

2) Clone the full GitHub repo, then navigate to the correct repo :

```bash
git clone git@github.com:lcls-mlcv/coyote_protector.git
cd /sdf/data/lcls/ds/mfx/exp_id/results/your/folder/to/process/images/coyote_protector/scripts/production/inference_xtc_parallel_pipeline
```
Now that the folder is on SDF, verify these values in `routine_detection_v3.sh`:

- `DEST_HOST="psana.sdf.slac.stanford.edu"`
- `SDF_BASE="/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_parallel_pipeline"`
- `RESULTS_BACK_BASE="/cds/data/iocDatas/..../..../"`

The SDF path is derived from `EXP_NUMBER`. The CDS destination should be updated to the local folder where you want CSV results copied back.

3) Rsync that SDF folder to CDS.
Connect to CDS and go to your CDS folder where you want final results stored, then run:

```bash
rsync -av "${USER_NAME}@${DEST_HOST}:/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_parallel_pipeline/" ./
```

4) (Optional) Passwordless SSH setup (CDS -> SDF)

Some steps in this pipeline connect multiple times to SDF (`psana.sdf.slac.stanford.edu`) using `ssh`.
If SSH keys are not configured, you will be prompted for your password repeatedly.

To avoid too many authentications, configure passwordless SSH from CDS to SDF before production runs.

-  Generate an SSH key on **CDS**:

```bash
ssh-keygen -t ed25519
```

Press `Enter` for all prompts to accept the default location:

```text
~/.ssh/id_ed25519
```

This creates:

```text
~/.ssh/id_ed25519
~/.ssh/id_ed25519.pub
```

You can verify the key files with:

```bash
ls -l ~/.ssh
cat ~/.ssh/id_ed25519.pub
```

- Authorize the public key on SDF:

```bash
ssh-copy-id <username>@psana.sdf.slac.stanford.edu
```

You will be asked for your password **once**. This adds the public key to:

```text
~/.ssh/authorized_keys
```

on SDF.

- Test the connection from CDS:

```bash
ssh <username>@psana.sdf.slac.stanford.edu
```

If the setup is correct, the login should not ask for a password.

---

5) Run the routine

- Source the environment on CDS : 
```bash
source /cds/group/pcds/pyps/conda/pcds_conda
```

- Then run :
```bash
python bash_launcher.py --user=<username> --run_number=<run_number> --exp_number=<experiment_id> --max_events=<max_events> --num_parts=<num_parts> --camera_name=<camera_name> > quick_run.log &
```

## Required configuration before production

Review these hardcoded values before production runs:

### 1) SLURM resources/accounts

- `run_export_infer_xtc_parallel.sh`
  - `#SBATCH --account=lcls:prjlumine22`
  - `#SBATCH --partition=milano`

- `run_export_infer_worker.sh`
  - `#SBATCH --account=lcls:prjatomicspi19`
  - `#SBATCH --partition=ada`
  - `#SBATCH --gpus=1`

Note : you must have the access to those partitions/ressources

### 2) Python environments

- psana env sourced in shell scripts:
  - `/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh`

- YOLO python binary used by worker:
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

Default values:
- `DEST_HOST="psana.sdf.slac.stanford.edu"`
- `SDF_BASE="/sdf/data/lcls/ds/mfx/${EXP_NUMBER}/results/coyote_protector/scripts/production/inference_xtc_parallel_pipeline"`
- `RESULTS_BACK_BASE="/cds/data/iocDatas/..../..../"`

---

## Run options

## A) Recommended: launch from CDS with Python wrapper

```bash
python bash_launcher.py \
  --user=<username> \
  --run_number=146 \
  --exp_number=mfx101232725 \
  --max_events=80000 \
  --num_parts=4 \
  --camera_name=inline_alvium
```

Dry-run (prints command only):

```bash
python bash_launcher.py --dry_run
```

This calls `routine_detection_v3.sh`, which submits the SDF master job and copies back `run_<run>_results/` to `RESULTS_BACK_BASE`.

## B) Directly on SDF: submit master job

```bash
sbatch run_export_infer_xtc_parallel.sh \
  RUN_NUMBER=146 \
  EXP_NUMBER=mfx101232725 \
  MAX_EVENTS=80000 \
  NUM_PARTS=4 \
  CAMERA_NAME=inline_alvium
```

---

## Monitoring and logs

Check jobs:

```bash
squeue -u $(whoami)
```

Master logs:

```bash
tail -f logs_export/export_infer_parallel_<jobid>.out
tail -f logs_export/export_infer_parallel_<jobid>.err
```

Worker logs:

```bash
tail -f logs_export/export_infer_worker_<jobid>.out
tail -f logs_export/export_infer_worker_<jobid>.err
```

---

## Output layout

Inside SDF run folder (`run_<RUN_NUMBER>/`):

- `timestamps_run_<RUN_NUMBER>.json`
- `timestamps_parts/timestamps_part_<i>.json`
- `part_<i>/...` (worker-local files)
- `results_csv_part_<i>/`
  - `event_data.csv`
  - `measurements_complete.csv`
  - `measurements_above_threshold.csv`
- `results_csv/` (merged final)
  - `event_data.csv`
  - `measurements_complete.csv`
  - `measurements_above_threshold.csv`
  - `merged_crystals.csv`

---

## Common issues

- `psana` import fails
  Source psana env before running export scripts:
  ```bash
  source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh
  ```

- YOLO inference fails to start
  Validate `YOLO_PYTHON` path in `run_export_infer_worker.sh` and `weights_path` in `inference_coyote_xtc.py`.

- Missing part outputs
  Confirm all workers produced both:
  - `results_csv_part_<i>/event_data.csv`
  - `results_csv_part_<i>/measurements_complete.csv`

- Merge script file-not-found
  Ensure merged files exist under `run_<run>/results_csv/` before final merge.

---

## Minimal reproducible command

```bash
sbatch run_export_infer_xtc_parallel.sh RUN_NUMBER=146 EXP_NUMBER=mfx101232725 MAX_EVENTS=100 NUM_PARTS=4 CAMERA_NAME=inline_alvium
```

When complete, inspect:

```bash
ls -lh run_146/results_csv/
```

---

## What this pipeline does in detail

1. Export run timestamps from XTC (`export_xtc_timestamps.py`)
2. Split timestamps into N chunks (`split_timestamps.py`)
3. Launch one SLURM worker per chunk (`run_export_infer_worker.sh`)
4. Each worker:
   - exports normalized PNGs + `event_data.csv` (`export_xtc_segmented_timestamps.py`)
   - runs YOLO inference (`inference_coyote_xtc.py`)
5. Master script merges part CSVs and builds `merged_crystals.csv` (`merge_crystals_data.py`)
6. Optional orchestrator from CDS pulls results back (`routine_detection_v3.sh`)

---

## Folder scripts

- `bash_launcher.py`
  Python launcher for `routine_detection_v3.sh` with CLI args.

- `routine_detection_v3.sh`
  Runs from CDS, SSHs to SDF, submits master SLURM job, waits for completion, and rsyncs results back.

- `run_export_infer_xtc_parallel.sh`
  Master SLURM job: timestamp export → split → worker submission → merge all part CSVs.

- `run_export_infer_worker.sh`
  Worker SLURM job for one timestamp chunk: export segmented images and run YOLO inference.

- `export_xtc_timestamps.py`
  Builds sorted timestamp list `timestamps_run_<run>.json`.

- `split_timestamps.py`
  Splits one timestamp JSON into `timestamps_part_*.json` files.

- `export_xtc_segmented_timestamps.py`
  Exports normalized PNGs and trajectory metadata for the assigned timestamps.

- `inference_coyote_xtc.py`
  Runs YOLO and writes:
  - `results_csv/measurements_complete.csv`
  - `results_csv/measurements_above_threshold.csv`

- `merge_crystals_data.py`
  Merges `event_data.csv` with `measurements_above_threshold.csv` into `merged_crystals.csv`.

---

## CSV schema summary

### `event_data.csv`

Columns:
- `event_id`
- `timestamp`
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

---

## Precise inputs/outputs by algorithm (reference)

This section is the contract for each script: exact runtime inputs, what it reads, and what it writes.

### 1) `export_xtc_timestamps.py`

**CLI input**

```bash
python export_xtc_timestamps.py [run_number] [exp_number] [max_events]
```

Defaults:
- `run_number=146`
- `exp_number=mfx101232725`
- `max_events=100`

**Reads**
- XTC stream from psana datasource: `DataSource(exp=..., run=[...], max_events=...)`

**Writes**
- `timestamps_run_<run_number>.json` in current working directory
  - JSON list of timestamps (sorted ascending)

**Output type**
- One JSON array (`list[int]`)

### 2) `split_timestamps.py`

**CLI input**

```bash
python split_timestamps.py <input_json> <n_parts> <out_dir>
```

**Reads**
- `<input_json>`: JSON list of timestamps

**Writes**
- `<out_dir>/timestamps_part_0.json`
- ...
- `<out_dir>/timestamps_part_<n_parts-1>.json`

**Output type**
- `n_parts` JSON arrays; each is a contiguous slice of the original list

### 3) `export_xtc_segmented_timestamps.py`

**CLI input**

```bash
python export_xtc_segmented_timestamps.py [run_number] [exp_number] [max_events] [camera_name] [timestamps_json] [original_timestamps_json]
```

Defaults:
- `run_number=146`
- `exp_number=mfx101232725`
- `max_events=100`
- `camera_name=inline_alvium`

**Reads**
- XTC stream through psana detectors:
  - camera: `camera_name` argument (default `inline_alvium`)
  - trajectories: `XTRAJ`, `YTRAJ`
- Optional timestamp subset file: `[timestamps_json]`
- Optional global timestamp file for stable ID mapping: `[original_timestamps_json]`

**Writes**
- `run_<run_number>_png_norm/event_<event_id>.png` (normalized PNGs)
- `run_<run_number>_png/event_data.csv`

`event_data.csv` columns:
- `event_id`
- `timestamp`
- `png_file`
- `xtraj`
- `ytraj`

**Output type**
- Image set + one CSV row per successfully exported event

### 4) `inference_coyote_xtc.py`

**CLI input**

```bash
python inference_coyote_xtc.py <chip_pic_dir>
```

**Reads**
- Input image directory `<chip_pic_dir>` (PNG files)
- YOLO weights from `weights_path` hardcoded in script

**Writes**
- `results_csv/measurements_complete.csv`
- `results_csv/measurements_above_threshold.csv`

CSV columns (both files):
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

Filtering rule:
- `measurements_above_threshold.csv` keeps only detections where `longest_um > alert_um`

**Output type**
- Detection-level CSV rows (one row per detection)

### 5) `merge_crystals_data.py`

**CLI input**

```bash
python merge_crystals_data.py [run_number]
```

Default:
- `run_number=146` (argument currently not used to build paths in this version)

**Reads**
- `results_csv/event_data.csv`
- `results_csv/measurements_above_threshold.csv`

Join key:
- `event_data.csv::png_file` renamed to `image`
- merge on `image`

**Writes**
- `results_csv/merged_crystals.csv`

Merged columns:
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

**Output type**
- Detection-level merged CSV (trajectory + detection features)

### 6) `run_export_infer_worker.sh`

**Runtime inputs (key=value)**
- `RUN_NUMBER`
- `EXP_NUMBER`
- `MAX_EVENTS`
- `PART_INDEX`
- `CAMERA_NAME`
- `TIMESTAMP_FILE`
- `ORIGINAL_TIMESTAMP_FILE`

**Reads**
- Timestamp part JSON from `TIMESTAMP_FILE`
- Global timestamp JSON from `ORIGINAL_TIMESTAMP_FILE`
- XTC via psana (through called Python script)
- YOLO model/path settings from called scripts and `YOLO_PYTHON`

**Writes**
- Worker-local export + inference artifacts
- Copies final worker products to:
  - `../results_csv_part_<PART_INDEX>/event_data.csv`
  - `../results_csv_part_<PART_INDEX>/measurements_complete.csv`
  - `../results_csv_part_<PART_INDEX>/measurements_above_threshold.csv`

### 7) `run_export_infer_xtc_parallel.sh`

**Runtime inputs (key=value)**
- `RUN_NUMBER`
- `EXP_NUMBER`
- `MAX_EVENTS`
- `NUM_PARTS`
- `CAMERA_NAME`

**Reads**
- Calls and consumes outputs from:
  - `export_xtc_timestamps.py`
  - `split_timestamps.py`
  - `run_export_infer_worker.sh` (`NUM_PARTS` times)

**Writes (under `run_<RUN_NUMBER>/`)**
- `timestamps_run_<RUN_NUMBER>.json`
- `timestamps_parts/timestamps_part_<i>.json`
- `results_csv_part_<i>/...` for each part
- merged final files in `results_csv/`:
  - `event_data.csv`
  - `measurements_complete.csv`
  - `measurements_above_threshold.csv`
  - `merged_crystals.csv`

### 8) `routine_detection_v3.sh` and `bash_launcher.py`

**Purpose**
- High-level orchestration only (CDS → SDF submission and copy-back)

**Runtime inputs**
- Via launcher args or key=value passthrough:
  - `USER`, `RUN_NUMBER`, `EXP_NUMBER`, `MAX_EVENTS`, `NUM_PARTS`, `CAMERA_NAME`

**Reads**
- Remote folder `SDF_BASE` and generated run outputs on SDF

**Writes**
- Copies `run_<RUN_NUMBER>/results_csv/` from SDF into local CDS destination:
  - `${RESULTS_BACK_BASE}/run_<RUN_NUMBER>_results/`
