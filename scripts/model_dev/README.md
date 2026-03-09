# Model Development Pipeline (YOLOv8 Crystal Detection)

This folder contains the end-to-end scripts used to prepare data, train a YOLOv8 model, run inference with crystal-size alerts, and evaluate model quality.

## Concept

Crystallography detectors are highly sensitive, and large crystals can cause serious damage if they are not identified in time. This pipeline uses YOLOv8 to analyze microscopy images, detect crystals, and estimate crystal size from bounding-box dimensions. Sizes are converted from pixels to microns using a calibration factor (`px_to_um`), and threshold-based alerts can be used to flag oversized crystals early.

### Key Highlights

- Manual and AI-assisted labeling workflow (LabelMe and SAM)
- Fine-tuned YOLOv8 model for crystal detection
- Pixel-to-micron size conversion and threshold alert logic
- Inference outputs with annotated detections and size metrics CSV

## Overview

The workflow mirrors the main project idea: detect crystals from microscopy images, estimate crystal size from bounding boxes, convert pixels to microns (`px_to_um`), and trigger a safety alert when crystals exceed a threshold.

### Included scripts

- `prepare_dataset.py`: Converts COCO annotations to YOLO labels, writes train/val splits, converts images to grayscale 3-channel, and generates `yolo_dataset.yaml`.
- `training.py`: Trains a YOLOv8 model (default: `yolov8n.pt`).
- `inference.py`: Runs inference, saves YOLO-rendered predictions, and exports detection size metrics to CSV.
- `eval_accuracy.py`: Runs validation and prints `mAP50`, precision, and recall.
- `utilities/`: Helper scripts for dataset tooling, including LabelMe-to-COCO conversion.
- `benchmarking/`: Optional speed/throughput benchmarking utilities.

## 1. Environment Setup

You have two options:

- Option A: create your own environment (recommended if you do not have access to `prjlumine22`).
- Option B: use the shared environment below if you have access to `prjlumine22`.

### Option A: Create your own environment

On S3DF (or any Linux machine):

```bash
conda create --name coyote_env python=3.10
conda activate coyote_env
conda install pytorch torchvision torchaudio cudatoolkit=12.2 -c pytorch
pip install ultralytics opencv-python matplotlib scikit-learn numpy
```

Optional (if using S3DF and Miniconda is not installed yet):

```bash
ssh yourusername@s3dflogin.slac.stanford.edu
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
```

Add this helper to your `.bashrc`:

```bash
init_conda () {
	source ~/miniconda3/etc/profile.d/conda.sh
}
init_conda
```

### Option B: Use the shared environment (if authorized)

Shared environment path:

```bash
conda activate /sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/
```

Use this option only if you are in (or have access to) the `prjlumine22` group.



## 2. Cloning the repo 

- Clone the repository:

```bash
git clone git@github.com:lcls-mlcv/coyote_protector.git
cd path/to/coyote_protector
```

## 3. Dataset Preparation

If you are retraining with new data, label images first:

```bash
pip install labelme
labelme path/to/images/
```

Labeling notes:
- For now, labeling is done locally (not on S3DF).
- Example image folder: `/sdf/home/p/pmonteil/data_coyote/images_prakriti_s3df`, those can be downloaded on your personnal device
- If LabelMe has compatibility issues, downgrade numpy:

```bash
pip install "numpy==1.24.*"
```

- Open LabelMe.
- Open the correct image folder.
- Draw rectangles around crystals.
- Save JSON annotations.
- Draw boxes manually or use AI prompt/SAM tools in LabelMe
- Adjust score/IoU thresholds as needed
- Save annotations in `.json` (you will have one `.json` per image).
- Then merge all LabelMe JSON files into one COCO-like JSON with:
	- `scripts/model_dev/utilities/converter.py`
- Before running the converter, update:
	- `LABELME_DIR`: folder containing all LabelMe JSON files on your device
	- `OUT_JSON`: output COCO-like JSON path on your device.
	- `ROOT_PREFIX`: prefix of the coyote image folder on the machine where you run training; if this is wrong, `file_name` paths will break.
- Run converter locally:

```bash
python scripts/model_dev/utilities/converter.py
```

- Use the generated COCO JSON as `coco_json_path` in `prepare_dataset.py`.
- Transfer labeled data to S3DF if needed:

```bash
scp -r path/to/labeled_dataset username@s3dflogin.slac.stanford.edu:path/to/project
```

Before training, keep a YOLO-compatible layout:

```text
images/
	train/
	val/
labels/
	train/
	val/
```

Practical project flow:

- Clone the repository:

```bash
git clone git@github.com:lcls-mlcv/coyote_protector.git
cd path/to/coyote_protector
```

- Put your annotation file in the training workspace (example):
  - `path/to/test_training/dataset.json`
- Run the converter script (`prepare_dataset.py`) after updating all 7 path variables.

Edit paths at the top of `prepare_dataset.py`:

```python
coco_json_path   = 'path/to/your/dataset_fixed.json'
chip_pic_dir     = 'path/to/your/chip_pic'
images_train_dir = 'path/to/your/yolo_dataset/images/train'
images_val_dir   = 'path/to/your/yolo_dataset/images/val'
labels_train_dir = 'path/to/your/yolo_dataset/labels/train'
labels_val_dir   = 'path/to/your/yolo_dataset/labels/val'
yaml_path        = 'path/to/your/yolo_dataset/yolo_dataset.yaml'
```

Run:

```bash
python scripts/model_dev/prepare_dataset.py
```

Expected output:

- YOLO-format labels (`.txt`) for train and val
- Grayscale 3-channel images for train and val
- `yolo_dataset.yaml`

## 4. Training

Edit `training.py`:

- `data=` should point to your generated `yolo_dataset.yaml`
- tune `epochs`, `imgsz`, and `batch` as needed

Run:

```bash
/sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/bin/python training.py
```

If you are using your own environment, activate it and run instead:

```bash
python training.py
```

If you get a permission error, ask to be added to the `prjlumine22` group.

Default YOLO output directory:

- `runs/detect/train/weights/best.pt`
- subsequent runs: `train2`, `train3`, etc.

## 5. Inference + Size Alert CSV

Edit `inference.py`:

- `weights_path`: trained `.pt` weights path
- `chip_pic_dir`: input image folder
- `px_to_um`: pixel-to-micron conversion factor
- `alert_um`: threshold for safety alert (default `100.0`)

Run:

```bash
python scripts/model_dev/inference.py
```

Outputs:

- CSV: `runs/size_metrics/measurements.csv`
- YOLO annotated images: `runs/detect/predict*/`
- Console alert lines when detections exceed threshold (`STOP`)

## Example


<img width="1201" height="614" alt="Screenshot 2025-07-21 at 3 08 19 PM" src="https://github.com/user-attachments/assets/f030985e-ce8f-454a-8050-8ff9f076d446" />

## 6. Model Evaluation

Edit `eval_accuracy.py`:

- model path in `YOLO(...)`
- `data=` path to your `yolo_dataset.yaml`

Run:

```bash
python scripts/model_dev/eval_accuracy.py
```

Metrics printed:

- `mAP50`
- `Precision`
- `Recall`

## Optional: Benchmarking

The `benchmarking/` directory contains additional utilities for model and ONNX thread benchmarking.

See:

- `scripts/model_dev/benchmarking/README.md`

## C++ Inference with ONNX Runtime

This repository also includes a C++ implementation in `yolov8_cpp/` for YOLO inference with ONNX Runtime and OpenCV. See:

- `path/to/coyote_protector/yolov8_cpp/README.md`

## Typical Run Order

1. `prepare_dataset.py`
2. `training.py`
3. `inference.py`
4. `eval_accuracy.py`
