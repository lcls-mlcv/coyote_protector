# Model Benchmark Catalog (Turing GPUs)

This README documents how model benchmarks were produced, which scripts were used, and where to find the result figures and summary tables.

## 1) What We Benchmarked

We evaluated four YOLO models on three evaluation splits:
- `all_images`
- `rod_only_images`
- `sharpB_images`

For each model and split, we track:
- Precision
- Recall
- mAP50
- Mean inference time on Turing GPUs (ms per image)

## 2) Models Used

The benchmark in this folder uses local copied weights:

| Model Name | Family | Weights Path | Trained On Dataset | Training Dataset Path |
|---|---|---|---|---|
| `yolov11n_2C` | YOLOv11n | `weights/yolov11n_2C_best.pt` | `all_datasets_merged_v4` (merged run104,mfx101232725  + run61 mfx101346325 + previous images) | `/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote/datasets/all_datasets_merged_v4` |
| `yolov8n_2C` | YOLOv8n | `weights/yolov8n_2C_best.pt` | `all_datasets_merged_v4` (merged run104,mfx101232725 + run61,mfx101346325 + previous images) | `/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote/datasets/all_datasets_merged_v4` |
| `yolo11n_rodes` | YOLOv11n | `weights/yolo11n_rodes_best.pt` | `rod_run104_mfx101232725_only` | `/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote/datasets/rod_run104_mfx101232725_only` |
| `yolov11n_sharpB_recent` | YOLOv11n | `weights/yolov11n_sharpB_recent_best.pt` | `sharpb_run61_mfx101346325_only` | `/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote/datasets/sharpb_run61_mfx101346325_only` |

Note : if the models have to be retrained, the images paths have to be modified in the .json associated before executing prepare_dataset.py. 

## 3) Benchmark Pipeline On Turing

We leveraged the project benchmarking scripts located in:
- `scripts/model_dev/benchmarking/benchmark_models.py`
- `scripts/model_dev/benchmarking/run_benchmark_models.sh`

How this is organized for Turing runs in `models/`:
- Outputs were generated into dedicated folders by split:
	- `benchmarks/benchmark_all_dataset/`
	- `benchmarks/benchmark_rod_only/`
	- `benchmarks/benchmark_sharpB_only/`

Run command used in this folder:

```bash
cd /sdf/home/p/pmonteil/coyote_protector/models
sbatch benchmarks/run_benchmark_turing.sh
```

## 4) Metrics Catalog

| Date | Model | Evaluation Split | Precision | Recall | mAP50 | Mean Inference Time on GPUs (Turing) [ms/image] | Source |
|---|---|---|---:|---:|---:|---:|---|
| 2026-02-11 | `yolov11n_2C` | `all_images` | 0.908 | 0.843 | 0.918 | 10.244 | `benchmarks/benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `all_images` | 0.884 | 0.890 | 0.919 | 7.823 | `benchmarks/benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `all_images` | 0.010 | 0.036 | 0.002 | 10.340 | `benchmarks/benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `all_images` | 0.334 | 0.371 | 0.342 | 10.069 | `benchmarks/benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov11n_2C` | `rod_only_images` | 0.636 | 0.064 | 0.346 | 8.323 | `benchmarks/benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `rod_only_images` | 1.000 | 0.091 | 0.545 | 6.387 | `benchmarks/benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `rod_only_images` | 0.764 | 0.782 | 0.810 | 8.604 | `benchmarks/benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `rod_only_images` | 0.096 | 0.191 | 0.094 | 8.907 | `benchmarks/benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_2C` | `sharpB_images` | 0.958 | 0.797 | 0.945 | 8.398 | `benchmarks/benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `sharpB_images` | 0.932 | 0.941 | 0.977 | 6.072 | `benchmarks/benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `sharpB_images` | 0.051 | 0.007 | 0.001 | 8.261 | `benchmarks/benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `sharpB_images` | 0.933 | 0.876 | 0.949 | 8.283 | `benchmarks/benchmark_sharpB_only/pareto_data.csv` |

## 5) Benchmark Figures

### All Dataset (`benchmarks/benchmark_all_dataset`)
- Pareto: `benchmarks/benchmark_all_dataset/pareto_speed_accuracy.png`
- Metrics histogram: `benchmarks/benchmark_all_dataset/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmarks/benchmark_all_dataset/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmarks/benchmark_all_dataset/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmarks/benchmark_all_dataset/runs_stats/violin_image_means_by_build.png`

<img width="600" height="450" alt="image" src="https://github.com/user-attachments/assets/aad16d12-a2e0-401f-bf47-cbd4857cbc24" />

### Rod Only (`benchmarks/benchmark_rod_only`)
- Pareto: `benchmarks/benchmark_rod_only/pareto_speed_accuracy.png`
- Metrics histogram: `benchmarks/benchmark_rod_only/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmarks/benchmark_rod_only/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmarks/benchmark_rod_only/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmarks/benchmark_rod_only/runs_stats/violin_image_means_by_build.png`

<img width="600" height="450" alt="image" src="https://github.com/user-attachments/assets/5d82e9ab-1d21-465e-a7b1-7f9dfa2aea9d" />


### SharpB Only (`benchmarks/benchmark_sharpB_only`)
- Pareto: `benchmarks/benchmark_sharpB_only/pareto_speed_accuracy.png`
- Metrics histogram: `benchmarks/benchmark_sharpB_only/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmarks/benchmark_sharpB_only/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmarks/benchmark_sharpB_only/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmarks/benchmark_sharpB_only/runs_stats/violin_image_means_by_build.png`

<img width="600" height="450" alt="image" src="https://github.com/user-attachments/assets/0c466aaa-915a-4e28-a502-173a0150e08f" />


## 6) Notes

- `all_images` captures broader behavior but can hide split-specific failure modes.
- `rod_only_images` and `sharpB_images` reveal class/domain sensitivity.
- Always compare both accuracy and runtime together when selecting a deployment model.

