# Model Catalog

This file is the catalog for detection models used in Coyote Protector experiments.

Use this page to track:
- Algorithm/model variant
- Weights used for inference
- Dataset configuration
- Evaluation metrics (precision/recall/mAP)

## 1) Algorithms (Models)
    
| Model Name | Family | Weights Path | Notes |
|---|---|---|---|
| `yolov11n_2C` | YOLOv11n | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v4_merged_run104_mfx101232725_run61_mfx101346325/scripts/runs/detect/train_150epochs_v11n/weights/best.pt` | Trained on merged 2-class setup with v11n|
| `yolov8n_2C` | YOLOv8n | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v4_merged_run104_mfx101232725_run61_mfx101346325/scripts/runs/detect/train_150epochs_v8n/weights/best.pt` | Trained on merged 2-class setup with 11n |
| `yolo11n_rodes` | YOLOv11n | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run104_mfx101232725_200first/scripts/runs/detect/train_mfx101232725_run104_rodelike_200first_every5rd_150epochs_v11n/weights/best.pt` | Rod-like focused dataset (run104 mfx101232725)|
| `yolov11n_sharpB_recent` | YOLOv11n | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/scripts/runs/detect/train_150epochs_v11_run61_only/weights/best.pt` | SharpB-focused (run61 mfx101346325) |

## 2) Dataset Catalog

| Dataset ID | YAML Path | Status | Comments |
|---|---|---|---|
| `all_datasets_merged_v4` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v4_merged_run104_mfx101232725_run61_mfx101346325/dataset/yolo_dataset.yaml` | Active | Full merged dataset |
| `rod_run104_only` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run104_mfx101232725_200first/dataset/yolo_dataset.yaml` | Correct | Rod-only dataset (run104 mfx101232725) |
| `sharpb_run61_only` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/dataset_run61_only/yolo_dataset.yaml` | Correct | SharpB-only dataset (run61 mfx101346325)|
| `run61_plus_prakriti` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/dataset_merged/yolo_dataset.yaml` | Needs verification | Mentioned as not shown in some results |

### Dataset metadata (from `dataset_merged/yolo_dataset.yaml`)

- `train`: `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/dataset_merged/images/train`
- `val`: `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/dataset_merged/images/val`
- `nc`: `1`
- `names`: `['crystals']`

## 3) Metrics Catalog

Results below are the stored benchmark values from the testing summary.

| Date | Model | Evaluation Split | Precision | Recall | mAP50 | Mean Inference Time on GPUs (Turing) [ms/image] | Notes |
|---|---|---|---:|---:|---:|---:|---|
| 2026-02-11 | `yolov11n_2C` | `all_images` | 0.908 | 0.843 | 0.918 | 8.46 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov11n_2C` | `rod_only_images` | 0.636 | 0.064 | 0.346 | 8.46 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov11n_2C` | `sharpB_images` | 0.958 | 0.797 | 0.945 | 8.46 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov8n_2C` | `all_images` | 0.884 | 0.890 | 0.919 | 6.17 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov8n_2C` | `rod_only_images` | 1.000 | 0.091 | 0.545 | 6.17 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov8n_2C` | `sharpB_images` | 0.932 | 0.941 | 0.977 | 6.17 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolo11n_rodes` | `rod_only_images` | 0.764 | 0.782 | 0.810 | 8.66 | Detection Approach - YOLO - Testing |
| 2026-02-11 | `yolov11n_sharpB_recent` | `sharpB_images` | 0.933 | 0.876 | 0.949 | 8.58 | Detection Approach - YOLO - Testing |

## 4) Suggested Evaluation Workflow

1. Select a model weights file from the Algorithms table or created on your own.
2. Select the target dataset YAML from the Dataset Catalog.
3. Run validation/inference and collect metrics from YOLO results.
4. Add one line to the Metrics Catalog with exact values and date.
5. Keep notes if the dataset differs from the expected split/classes.

