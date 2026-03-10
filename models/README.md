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

| Model Name | Family | Weights Path | Trained On Dataset | Training Dataset YAML Path |
|---|---|---|---|---|
| `yolov11n_2C` | YOLOv11n | `weights/yolov11n_2C_best.pt` | `all_datasets_merged_v4` (merged run104 + run61 + previous images) | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v4_merged_run104_mfx101232725_run61_mfx101346325/dataset/yolo_dataset.yaml` |
| `yolov8n_2C` | YOLOv8n | `weights/yolov8n_2C_best.pt` | `all_datasets_merged_v4` (merged run104 + run61) + previous images | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v4_merged_run104_mfx101232725_run61_mfx101346325/dataset/yolo_dataset.yaml` |
| `yolo11n_rodes` | YOLOv11n | `weights/yolo11n_rodes_best.pt` | `rod_run104_only` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run104_mfx101232725_200first/dataset/yolo_dataset.yaml` |
| `yolov11n_sharpB_recent` | YOLOv11n | `weights/yolov11n_sharpB_recent_best.pt` | `sharpb_run61_only` | `/sdf/home/p/pmonteil/coyote_protector_test_PL_labeling_tries_v3_run61_mfx101346325_200_random/dataset_run61_only/yolo_dataset.yaml` |

## 3) Benchmark Pipeline On Turing

We leveraged the project benchmarking scripts located in:
- `scripts/model_dev/benchmarking/benchmark_models.py`
- `scripts/model_dev/benchmarking/run_benchmark_models.sh`

How this was used for Turing runs in `models/`:
- The same benchmark logic (accuracy + speed + Pareto) was reused in `benchmark.py`.
- The job launch was adapted for Turing GPU execution with `run_benchmark_turing.sh`.
- Outputs were generated into dedicated folders by split:
	- `benchmark_all_dataset/`
	- `benchmark_rod_only/`
	- `benchmark_sharpB_only/`

Run command used in this folder:

```bash
cd /sdf/home/p/pmonteil/coyote_protector/models
sbatch run_benchmark_turing.sh
```

## 4) Metrics Catalog

| Date | Model | Evaluation Split | Precision | Recall | mAP50 | Mean Inference Time on GPUs (Turing) [ms/image] | Source |
|---|---|---|---:|---:|---:|---:|---|
| 2026-02-11 | `yolov11n_2C` | `all_images` | 0.908 | 0.843 | 0.918 | 10.244 | `benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `all_images` | 0.884 | 0.890 | 0.919 | 7.823 | `benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `all_images` | 0.010 | 0.036 | 0.002 | 10.340 | `benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `all_images` | 0.334 | 0.371 | 0.342 | 10.069 | `benchmark_all_dataset/pareto_data.csv` |
| 2026-02-11 | `yolov11n_2C` | `rod_only_images` | 0.636 | 0.064 | 0.346 | 8.323 | `benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `rod_only_images` | 1.000 | 0.091 | 0.545 | 6.387 | `benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `rod_only_images` | 0.764 | 0.782 | 0.810 | 8.604 | `benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `rod_only_images` | 0.096 | 0.191 | 0.094 | 8.907 | `benchmark_rod_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_2C` | `sharpB_images` | 0.958 | 0.797 | 0.945 | 8.398 | `benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolov8n_2C` | `sharpB_images` | 0.932 | 0.941 | 0.977 | 6.072 | `benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolo11n_rodes` | `sharpB_images` | 0.051 | 0.007 | 0.001 | 8.261 | `benchmark_sharpB_only/pareto_data.csv` |
| 2026-02-11 | `yolov11n_sharpB_recent` | `sharpB_images` | 0.933 | 0.876 | 0.949 | 8.283 | `benchmark_sharpB_only/pareto_data.csv` |

## 5) Benchmark Figures

### All Dataset (`benchmark_all_dataset`)
- Pareto: `benchmark_all_dataset/pareto_speed_accuracy.png`
- Metrics histogram: `benchmark_all_dataset/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmark_all_dataset/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmark_all_dataset/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmark_all_dataset/runs_stats/violin_image_means_by_build.png`

<img width="1201" alt="All Dataset Pareto" src="benchmark_all_dataset/pareto_speed_accuracy.png" />

### Rod Only (`benchmark_rod_only`)
- Pareto: `benchmark_rod_only/pareto_speed_accuracy.png`
- Metrics histogram: `benchmark_rod_only/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmark_rod_only/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmark_rod_only/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmark_rod_only/runs_stats/violin_image_means_by_build.png`

<img width="1201" alt="Rod Only Pareto" src="benchmark_rod_only/pareto_speed_accuracy.png" />

### SharpB Only (`benchmark_sharpB_only`)
- Pareto: `benchmark_sharpB_only/pareto_speed_accuracy.png`
- Metrics histogram: `benchmark_sharpB_only/metrics/metrics_histogram_seaborn.png`
- Violin (run-level): `benchmark_sharpB_only/runs_stats/violin_runs_by_build.png`
- Violin (pooled image times): `benchmark_sharpB_only/runs_stats/violin_image_pooled_by_build.png`
- Violin (image mean times): `benchmark_sharpB_only/runs_stats/violin_image_means_by_build.png`

<img width="1201" alt="SharpB Only Pareto" src="benchmark_sharpB_only/pareto_speed_accuracy.png" />

## 6) Notes

- `all_images` captures broader behavior but can hide split-specific failure modes.
- `rod_only_images` and `sharpB_images` reveal class/domain sensitivity.
- Always compare both accuracy and runtime together when selecting a deployment model.

