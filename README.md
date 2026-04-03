# Coyote Protector

High-level toolkit for crystal detection on microscopy images using YOLO, with size-based safety alerts, model benchmarking, and XTC production pipelines for LCLS workflows.

## Core purpose

Use this repository to:

1. Develop and validate crystal-detection models.
2. Compare models for speed vs accuracy.
3. Run production inference pipelines on XTC data.
4. Deploy inference in C++ with ONNX Runtime.

## High-level repository map

```text
coyote_protector/
|- scripts/model_dev/    # R&D workflows: data prep, training, inference, evaluation
|- scripts/production/   # Production XTC pipelines (parallel + legacy serial)
|- models/               # Benchmark reports, model comparison context, archived results
|- yolov8_cpp/           # C++ ONNX Runtime inference path
`- requirements.txt      # Python dependencies for development/benchmarking
```

## What to use and when

- Use `scripts/model_dev/` when building or improving a model.
- Use `scripts/model_dev/benchmarking/` when selecting a model based on runtime and detection quality.
- Use `models/` when reviewing benchmark outcomes and historical model performance.
- Use `scripts/production/inference_xtc_parallel_pipeline/` for operational runs at scale (recommended).
- Use `scripts/production/inference_xtc_serial_pipeline/` only for legacy compatibility.
- Use `yolov8_cpp/` for C++/ONNX deployment scenarios.

## Typical lifecycle

1. Prepare/curate data and labels.
2. Train and validate candidate models.
3. Benchmark candidates and choose deployment model.
4. Run production pipeline on target runs.
5. Monitor outputs and iterate model updates when needed.

## Outputs you can expect

- Detection predictions and size measurements.
- Accuracy metrics (such as mAP50, precision, recall).
- Speed statistics and Pareto-style speed/accuracy comparisons.
- Production CSV outputs for downstream operational use.

## Detailed docs

- `scripts/model_dev/README.md`
- `scripts/model_dev/benchmarking/README.md`
- `scripts/production/inference_xtc_parallel_pipeline/README.md`
- `scripts/production/inference_xtc_serial_pipeline/README.md`
- `models/README.md`
- `yolov8_cpp/README.md`

## Notes

- The parallel production pipeline is the default path for new operational runs.
- Most scripts rely on environment-specific paths and compute settings; adapt them to your infrastructure.

