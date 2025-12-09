#!/usr/bin/env python3
"""
benchmark.py

Unified benchmark script for YOLO models:

1) Accuracy metrics (Python Ultralytics):
   - Runs model.val() on a YOLO dataset
   - Saves mAP50, Precision, Recall for each model (CSV + bar plot)

2) Inference speed benchmark (Python Ultralytics, multi-run):
   - For each model and each run:
       * Runs inference on a chip_pic_dir (all images)
       * Saves per-image inference times to summary.csv
       * Saves detection-based measurements (pixel/µm sizes, alerts) once per model
   - Aggregates across runs:
       * Run-level stats
       * Pooled per-image stats
       * Per-image mean across runs
       * Multi-model violin plots

3) Speed–Accuracy Pareto plot:
   - Merges accuracy (mAP50) with speed (mean_of_means_ms)
   - Saves pareto_speed_accuracy.png

All outputs are written under the directory:
   ./benchmark/
"""

import os
import sys
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from ultralytics import YOLO

# Headless plotting for clusters
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


# ============================================================
# USER SETTINGS
# ============================================================

# Dataset for YOLO val()

DATA_YAML = "path/to/yolo_dataset.yaml"
# Models to benchmark (update paths as needed)
# path to models and weights paths with the following format:

"""
MODELS = [
    {"name": "model1", "weights_path": "path/to/runs/detect/train_model1/weights/best.pt"},
    {"name": "model2", "weights_path": "path/to/runs/detect/train_model2/weights/best.pt"},
    {"name": "model3", "weights_path": "path/to/runs/detect/train_model3/weights/best.pt"},
    {"name": "model4", "weights_path": "path/to/runs/detect/train_model4/weights/best.pt"},
]
"""
MODELS = []
# Directory with chip images for speed benchmark
CHIP_PIC_DIR = "/path/to/chip_pics"

# Pixel → micron conversion
PX_TO_UM = 0.5
ALERT_UM = 100.0

# Number of repeated runs for speed benchmark
N_RUNS = 2

# Root directory for ALL outputs
ROOT_BASE = Path("benchmark_models")
ROOT_BASE.mkdir(parents=True, exist_ok=True)

# Subdirectory for metrics (accuracy)
METRICS_DIR = ROOT_BASE / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# Subdirectory for speed runs (inference time, violins, etc.)
RUNS_DIR = ROOT_BASE / "runs_stats"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Helper: violin plotting with mean/std
# ============================================================
def add_violin_with_mean_std(ax, data_arrays, labels, title, ylabel, outfile):
    """
    Multi-violin plot with:
      - violin per data array
      - mean line
      - ±1σ band
      - mean point w/ errorbar
      - median/min/max markers
      - text (mean/median/min/max)
    """
    if not data_arrays:
        return False

    K = len(data_arrays)
    positions = np.arange(1, K + 1, dtype=float)

    ax.violinplot(
        data_arrays,
        positions=positions,
        showmeans=False,
        showextrema=True,
        showmedians=False
    )

    global_min = np.inf
    global_max = -np.inf

    for i, arr in enumerate(data_arrays, start=1):
        arr = np.asarray(arr, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            continue

        m = float(np.mean(arr))
        sd = float(np.std(arr, ddof=0))
        med = float(np.median(arr))
        amin = float(np.min(arr))
        amax = float(np.max(arr))

        global_min = min(global_min, amin)
        global_max = max(global_max, amax)

        # mean line
        ax.hlines(m, i - 0.2, i + 0.2, linewidth=2)

        # ±1σ band
        ax.fill_between(
            [i - 0.2, i + 0.2],
            [m - sd, m - sd],
            [m + sd, m + sd],
            alpha=0.15
        )

        # mean point + errorbar
        ax.errorbar([i], [m], yerr=[sd], fmt="o", capsize=6)

        # median / min / max markers
        ax.hlines(med, i - 0.15, i + 0.15, linestyles="--", linewidth=1)
        ax.hlines(amin, i - 0.1,  i + 0.1,  linewidth=1)
        ax.hlines(amax, i - 0.1,  i + 0.1,  linewidth=1)

        # text with stats
        local_range = max(amax - amin, 1e-6)
        y_text = amax + 0.05 * local_range
        text = f"μ={m:.2f}\nmed={med:.2f}\nmin={amin:.2f}\nmax={amax:.2f}"
        ax.text(i, y_text, text, ha="center", va="bottom", fontsize=7)

    if np.isfinite(global_min) and np.isfinite(global_max):
        yr = max(global_max - global_min, 1e-6)
        ax.set_ylim(global_min - 0.05 * yr, global_max + 0.35 * yr)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(outfile, dpi=160)
    plt.close(ax.figure)
    return True


# ============================================================
# 1) ACCURACY METRICS VIA model.val()
# ============================================================
def run_accuracy_benchmark():
    print("\n=== Step 1: Accuracy benchmark via YOLO.val() ===\n")

    metrics_rows = []

    for cfg in MODELS:
        model_name = cfg["name"]
        weights_path = cfg["weights_path"]

        print(f"\n==============================")
        print(f"Validating model: {model_name}")
        print(f"Weights: {weights_path}")
        print(f"==============================\n")

        model = YOLO(weights_path)
        results = model.val(data=DATA_YAML)

        mAP50 = float(results.box.map50)
        prec = float(results.box.mp)
        recall = float(results.box.mr)

        print(f"[{model_name}] mAP50: {mAP50:.3f}")
        print(f"[{model_name}] Precision: {prec:.3f}")
        print(f"[{model_name}] Recall: {recall:.3f}")

        metrics_rows.append({"Model": model_name, "Metric": "mAP50", "Value": mAP50})
        metrics_rows.append({"Model": model_name, "Metric": "Precision", "Value": prec})
        metrics_rows.append({"Model": model_name, "Metric": "Recall", "Value": recall})

    df_long = pd.DataFrame(metrics_rows)
    csv_long = METRICS_DIR / "metrics_long.csv"
    df_long.to_csv(csv_long, index=False)

    df_wide = df_long.pivot(index="Model", columns="Metric", values="Value").reset_index()
    csv_wide = METRICS_DIR / "metrics_wide.csv"
    df_wide.to_csv(csv_wide, index=False)

    print(f"\nSaved accuracy metrics to:")
    print(f"  {csv_long}")
    print(f"  {csv_wide}")

    # Grouped bar chart
    plt.figure(figsize=(10, 5))
    sns.set_style("whitegrid")

    ax = sns.barplot(
        data=df_long,
        x="Model",
        y="Value",
        hue="Metric",
        errorbar=None
    )

    ax.set_title("YOLO Model Comparison (mAP50, Precision, Recall)", fontsize=14)
    ax.set_ylabel("Metric Value", fontsize=12)
    ax.set_xlabel("Model", fontsize=12)
    ax.set_ylim(0, 1)
    plt.legend(title="Metric")

    plt.tight_layout()
    plot_path = METRICS_DIR / "metrics_histogram_seaborn.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()

    print(f"Saved metrics bar chart to: {plot_path}")

    return df_wide  # for later Pareto merge


# ============================================================
# 2) SPEED BENCHMARK (MULTI-RUN INFERENCE)
# ============================================================
def run_speed_benchmark():
    print("\n=== Step 2: Speed benchmark with N runs per model ===\n")

    for cfg in MODELS:
        model_name = cfg["name"]
        weights_path = cfg["weights_path"]

        print(f"\n==============================")
        print(f"Benchmarking model: {model_name}")
        print(f"Weights: {weights_path}")
        print(f"==============================\n")

        # Per-model root (this is the "build" dir)
        root_out = RUNS_DIR / model_name
        root_out.mkdir(parents=True, exist_ok=True)

        # Load YOLO model for this set of weights
        model = YOLO(weights_path)

        # One-time: size output CSV (detections) for this model
        main_csv = root_out / "measurements.csv"
        sizes_written = False   # write detection sizes only during the FIRST run

        # ---------- MAIN LOOP OVER RUNS FOR THIS MODEL ----------
        for run_id in range(1, N_RUNS + 1):
            print(f"\n[{model_name}] RUN {run_id}/{N_RUNS}")

            run_dir = root_out / f"output_run{run_id:02d}"
            run_dir.mkdir(parents=True, exist_ok=True)

            summary_csv = run_dir / "summary.csv"

            # YOLO inference
            results = model.predict(
                source=CHIP_PIC_DIR,
                save=(run_id == N_RUNS),
                verbose=True
            )

            # Per-run summary.csv (filename, infer_ms)
            with open(summary_csv, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "infer_ms"])

                for r in results:
                    infer_ms = r.speed["inference"] if r.speed else float("nan")
                    img_name = os.path.basename(r.path)
                    writer.writerow([img_name, f"{infer_ms:.4f}"])

            print(f"[{model_name}][Run {run_id}] summary.csv → {summary_csv}")

            # Detection measurements only once per model
            if not sizes_written:
                with open(main_csv, "w", newline="") as f:
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
                            longest_um = longest_px * PX_TO_UM

                            cls_id = int(clses[i]) if clses.size > i else -1
                            cls_name = model.names.get(cls_id, str(cls_id)) if hasattr(model, "names") else str(cls_id)
                            conf = float(confs[i]) if confs.size > i else float("nan")

                            alert_flag = "STOP" if longest_um > ALERT_UM else ""

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

                sizes_written = True
                print(f"[{model_name}] measurements.csv saved → {main_csv}")

        print(f"\n[{model_name}] All runs completed.")
        for i in range(1, N_RUNS + 1):
            print(f" - {root_out}/output_run{i:02d}/summary.csv")

    # ---------- CROSS-MODEL AGGREGATION ----------
    print("\n=== Aggregating all models and generating speed plots ===")

    per_build = {}  # model_name -> stats dict

    for cfg in MODELS:
        model_name = cfg["name"]
        build_dir = RUNS_DIR / model_name

        run_dirs = sorted(build_dir.glob("output_run*"))
        if not run_dirs:
            print(f"[WARN] No runs found for model {model_name} in {build_dir}", file=sys.stderr)
            continue

        run_avgs = []
        img_rows = []

        for rd in run_dirs:
            sc = rd / "summary.csv"
            if not sc.exists():
                print(f"[WARN] summary.csv not found in {rd}", file=sys.stderr)
                continue

            dfi = pd.read_csv(sc)
            if not {"filename", "infer_ms"}.issubset(dfi.columns):
                print(f"[WARN] Missing columns in {sc}", file=sys.stderr)
                continue

            dfi["infer_ms"] = pd.to_numeric(dfi["infer_ms"], errors="coerce")
            dfi = dfi.dropna(subset=["infer_ms"])
            if len(dfi) == 0:
                continue

            run_avgs.append(float(dfi["infer_ms"].mean()))
            img_rows.append(dfi[["filename", "infer_ms"]])

        if not img_rows:
            print(f"[WARN] No valid data for model {model_name}", file=sys.stderr)
            continue

        df_all = pd.concat(img_rows, ignore_index=True)

        run_avgs = np.array(run_avgs, dtype=float)
        img_vals_pooled = df_all["infer_ms"].to_numpy(dtype=float)
        img_means = (
            df_all.groupby("filename")["infer_ms"]
                  .mean()
                  .to_numpy(dtype=float)
        )

        per_build[model_name] = {
            "run_avgs": run_avgs,
            "img_vals_pooled": img_vals_pooled,
            "img_means": img_means,
            "n_runs": len(run_dirs),
        }

        print(f"[INFO] {model_name}: runs={len(run_dirs)}, "
              f"run_avgs={run_avgs.size}, "
              f"img_vals={img_vals_pooled.size}, "
              f"img_means={img_means.size}")

    if not per_build:
        print("[ERROR] No valid data found for any model. Nothing to aggregate.", file=sys.stderr)
        sys.exit(1)

    outdir = RUNS_DIR
    os.makedirs(outdir, exist_ok=True)

    # 1) Run-level stats per model
    rows_run = []
    for name, s in per_build.items():
        arr = s["run_avgs"]
        if arr.size == 0:
            continue
        rows_run.append({
            "build": name,
            "n_runs": s["n_runs"],
            "n_avgs": arr.size,
            "mean_run_avg_ms": float(np.mean(arr)),
            "std_run_avg_ms": float(np.std(arr, ddof=0)),
        })
    if rows_run:
        df_runs = pd.DataFrame(rows_run).sort_values("build")
        df_runs.to_csv(outdir / "build_run_level_stats.csv", index=False)

    # 2) Pooled per-image values per model
    rows_img_pool = []
    for name, s in per_build.items():
        arr = s["img_vals_pooled"]
        if arr.size == 0:
            continue
        rows_img_pool.append({
            "build": name,
            "n_vals": arr.size,
            "mean_pooled_ms": float(np.mean(arr)),
            "std_pooled_ms": float(np.std(arr, ddof=0)),
        })
    if rows_img_pool:
        df_pool = pd.DataFrame(rows_img_pool).sort_values("build")
        df_pool.to_csv(outdir / "build_image_pooled_stats.csv", index=False)

    # 3) Per-image means across runs per model
    rows_img_means = []
    for name, s in per_build.items():
        arr = s["img_means"]
        if arr.size == 0:
            continue
        rows_img_means.append({
            "build": name,
            "n_images": arr.size,
            "mean_of_means_ms": float(np.mean(arr)),
            "std_of_means_ms": float(np.std(arr, ddof=0)),
        })
    df_imgm = None
    if rows_img_means:
        df_imgm = pd.DataFrame(rows_img_means).sort_values("build")
        df_imgm.to_csv(outdir / "build_image_means_stats.csv", index=False)

    # ---------- Multi-model violin plots ----------
    build_names = [cfg["name"] for cfg in MODELS if cfg["name"] in per_build]

    # Run-level violins
    data_run = [per_build[name]["run_avgs"] for name in build_names if per_build[name]["run_avgs"].size > 0]
    labels_run = [name for name in build_names if per_build[name]["run_avgs"].size > 0]
    if data_run:
        fig, ax = plt.subplots(figsize=(10, 5))
        add_violin_with_mean_std(
            ax,
            data_run,
            labels_run,
            title="Run-level average inference time per model",
            ylabel="avg_infer_ms (per run)",
            outfile=str(outdir / "violin_runs_by_build.png")
        )

    # Per-image pooled violins
    data_img_pooled = [per_build[name]["img_vals_pooled"] for name in build_names if per_build[name]["img_vals_pooled"].size > 0]
    labels_img_pooled = [name for name in build_names if per_build[name]["img_vals_pooled"].size > 0]
    if data_img_pooled:
        fig, ax = plt.subplots(figsize=(10, 5))
        add_violin_with_mean_std(
            ax,
            data_img_pooled,
            labels_img_pooled,
            title="Per-image inference times (pooled) by model",
            ylabel="infer_ms (per image)",
            outfile=str(outdir / "violin_image_pooled_by_build.png")
        )

    # Per-image mean across runs violins
    data_img_means = [per_build[name]["img_means"] for name in build_names if per_build[name]["img_means"].size > 0]
    labels_img_means = [name for name in build_names if per_build[name]["img_means"].size > 0]
    if data_img_means:
        fig, ax = plt.subplots(figsize=(10, 5))
        add_violin_with_mean_std(
            ax,
            data_img_means,
            labels_img_means,
            title="Per-image MEAN inference time across runs by model",
            ylabel="mean_infer_ms (per image)",
            outfile=str(outdir / "violin_image_means_by_build.png")
        )

    print("\nSpeed aggregation complete.")
    print(f"CSVs and PNGs in: {outdir}")

    return df_imgm  # for Pareto merge


# ============================================================
# 3) PARETO PLOT (SPEED VS ACCURACY)
# ============================================================
def make_pareto_plot(df_metrics_wide, df_speed_img_means):
    """
    Merge accuracy (mAP50) and speed (mean_of_means_ms) and
    generate a speed–accuracy Pareto plot.
    """
    if df_metrics_wide is None or df_speed_img_means is None:
        print("[WARN] Cannot generate Pareto plot (missing data).")
        return

    # df_metrics_wide: columns ["Model", "mAP50", "Precision", "Recall"]
    # df_speed_img_means: columns ["build", "n_images", "mean_of_means_ms", "std_of_means_ms"]

    df_speed = df_speed_img_means.rename(columns={"build": "Model"})
    df_merged = pd.merge(df_metrics_wide, df_speed, on="Model", how="inner")

    if df_merged.empty:
        print("[WARN] No overlapping models between metrics and speed. Skipping Pareto plot.")
        return

    pareto_csv = ROOT_BASE / "pareto_data.csv"
    df_merged.to_csv(pareto_csv, index=False)
    print(f"Saved Pareto data to: {pareto_csv}")

    # Plot: x = mean_of_means_ms (speed), y = mAP50 (accuracy)
    plt.figure(figsize=(8, 6))
    x = df_merged["mean_of_means_ms"].values
    y = df_merged["mAP50"].values
    labels = df_merged["Model"].values

    plt.scatter(x, y, s=120)

    for xi, yi, label in zip(x, y, labels):
        plt.text(xi + 0.2, yi, label, fontsize=11, va="center")

    plt.xlabel("Inference Time (mean_of_means_ms per image)")
    plt.ylabel("mAP@0.5")
    plt.title("Speed–Accuracy Pareto Frontier for YOLO Models")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    pareto_png = ROOT_BASE / "pareto_speed_accuracy.png"
    plt.savefig(pareto_png, dpi=300)
    plt.close()
    print(f"Saved Pareto plot to: {pareto_png}")


# ============================================================
# MAIN
# ============================================================
def main():
    # 1) Accuracy (val)
    df_metrics_wide = run_accuracy_benchmark()

    # 2) Speed (multi-run inference)
    df_speed_img_means = run_speed_benchmark()

    # 3) Pareto
    make_pareto_plot(df_metrics_wide, df_speed_img_means)


if __name__ == "__main__":
    main()
