#!/usr/bin/env python3
"""
onnx_threads_benchmark.py

Two modes:

1) RUN MODE
   python onnx_threads_benchmark.py run <model.onnx> <images_dir> <threads> <run_id>

   - Runs ONNX Runtime inference on all images in <images_dir>
   - Uses so.intra_op_num_threads = <threads>
   - Records per-image inference times (ms) into:
       benchmark_cpu_onnx_threads/onnx_infer_times.csv

   CSV columns:
       config_threads, run_id, image, infer_ms

2) PLOT MODE
   python onnx_threads_benchmark.py plot

   - Reads benchmark_cpu_onnx_threads/onnx_infer_times.csv
   - Generates a violin plot by thread configuration:
       benchmark_cpu_onnx_threads/violin_infer_time_by_threads.png
   - Also writes a summary CSV per configuration:
       benchmark_cpu_onnx_threads/onnx_infer_summary_per_config.csv
"""

import os
import sys
import glob
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ===========================
# Parameters (same as C++)
# ===========================
INPUT_W = 640
INPUT_H = 640
CONF_THR = 0.25      # unused here (no postproc)
IOU_THR = 0.45       # unused here
MATCH_IOU = 0.50     # unused here

# ===========================
# Output paths
# ===========================
BASE_DIR = Path("benchmark_cpu_onnx_threads")
BASE_DIR.mkdir(exist_ok=True)
CSV_PATH = BASE_DIR / "onnx_infer_times.csv"
SUMMARY_CFG_CSV_PATH = BASE_DIR / "onnx_infer_summary_per_config.csv"
VIOLIN_PNG_PATH = BASE_DIR / "violin_infer_time_by_threads.png"


# ===========================
# Helpers
# ===========================
def letterbox_bgr_to_rgb_640(img_bgr):
    h, w = img_bgr.shape[:2]
    r = min(INPUT_W / w, INPUT_H / h)
    new_w = int(round(w * r))
    new_h = int(round(h * r))

    pad_x = (INPUT_W - new_w) // 2
    pad_y = (INPUT_H - new_h) // 2

    resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((INPUT_H, INPUT_W, 3), 114, dtype=np.uint8)
    canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w, :] = resized

    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    return rgb


def list_images(folder):
    exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff")
    files = []
    for e in exts:
        files += glob.glob(os.path.join(folder, e))
    return sorted(files)


def run_single_config(model_path, images_dir, threads, run_id):
    """
    Run ONNX inference over all images for a given intra_op_num_threads and run_id,
    record per-image times, and append to CSV_PATH.
    """
    images = list_images(images_dir)
    if not images:
        print("[ERROR] No images found in:", images_dir)
        sys.exit(1)

    print(f"[CONFIG] Threads = {threads}, run_id = {run_id}")
    print(f"[CONFIG] Model   = {model_path}")
    print(f"[CONFIG] Images  = {images_dir}")
    print(f"[CONFIG] Count   = {len(images)}")

    # ===========================
    # ONNX Runtime session config
    # ===========================
    so = ort.SessionOptions()
    # so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.enable_mem_pattern = True
    so.intra_op_num_threads = int(threads)
    so.inter_op_num_threads = 1
    so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    so.log_severity_level = 3  # warnings+

    session = ort.InferenceSession(
        model_path,
        sess_options=so,
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name

    # Preallocate input tensor buffer
    in_buffer = np.zeros((1, 3, INPUT_H, INPUT_W), dtype=np.float32)

    def pack_chw(rgb):
        rgb_f32 = rgb.astype(np.float32) / 255.0
        in_buffer[0, 0, :, :] = rgb_f32[:, :, 0]
        in_buffer[0, 1, :, :] = rgb_f32[:, :, 1]
        in_buffer[0, 2, :, :] = rgb_f32[:, :, 2]

    # ===========================
    # Warmup
    # ===========================
    first = cv2.imread(images[0])
    if first is None:
        print("[ERROR] Failed to read first image:", images[0])
        sys.exit(1)
    rgb = letterbox_bgr_to_rgb_640(first)
    pack_chw(rgb)
    _ = session.run(None, {input_name: in_buffer})  # warmup

    # ===========================
    # Process images
    # ===========================
    times_ms = []
    img_names = []

    for path in images:
        img = cv2.imread(path)
        if img is None:
            print("[WARN] Failed to read:", path)
            continue

        rgb = letterbox_bgr_to_rgb_640(img)
        pack_chw(rgb)

        t0 = time.perf_counter()
        _ = session.run(None, {input_name: in_buffer})
        t1 = time.perf_counter()

        dt_ms = (t1 - t0) * 1000.0
        times_ms.append(dt_ms)
        img_names.append(os.path.basename(path))

    if not times_ms:
        print("[ERROR] No successful inference timings, aborting.")
        sys.exit(1)

    avg_ms = float(sum(times_ms) / len(times_ms))
    print(f"[RESULT] Threads={threads}, run_id={run_id} -> {len(times_ms)} images, avg={avg_ms:.3f} ms")

    # Append to CSV
    df_run = pd.DataFrame({
        "config_threads": [int(threads)] * len(times_ms),
        "run_id": [int(run_id)] * len(times_ms),
        "image": img_names,
        "infer_ms": times_ms,
    })

    if CSV_PATH.exists():
        df_run.to_csv(CSV_PATH, mode="a", header=False, index=False)
    else:
        df_run.to_csv(CSV_PATH, mode="w", header=True, index=False)


def plot_violin():
    if not CSV_PATH.exists():
        print("[ERROR] No CSV found at", CSV_PATH, "- nothing to plot.")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    if df.empty:
        print("[ERROR] CSV is empty - nothing to plot.")
        sys.exit(1)

    # ---- Summary per configuration (pooled across runs) ----
    summary_rows = []
    for threads, group in df.groupby("config_threads"):
        vals = group["infer_ms"].to_numpy(dtype=float)
        summary_rows.append({
            "config_threads": int(threads),
            "n_samples": len(vals),
            "mean_ms": float(np.mean(vals)),
            "std_ms": float(np.std(vals, ddof=0)),
            "min_ms": float(np.min(vals)),
            "max_ms": float(np.max(vals)),
        })

    df_summary_cfg = pd.DataFrame(summary_rows).sort_values("config_threads")
    df_summary_cfg.to_csv(SUMMARY_CFG_CSV_PATH, index=False)
    print("[INFO] Wrote config-level summary CSV to:", SUMMARY_CFG_CSV_PATH)

    # Prepare data for violin plot (per config, pooling runs)
    configs = df_summary_cfg["config_threads"].tolist()
    data_arrays = []
    labels = []

    for cfg in configs:
        vals = df[df["config_threads"] == cfg]["infer_ms"].to_numpy(dtype=float)
        data_arrays.append(vals)
        labels.append(str(cfg))

    fig, ax = plt.subplots(figsize=(10, 5))

    positions = np.arange(1, len(data_arrays) + 1, dtype=float)
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

        ax.hlines(m, i - 0.2, i + 0.2, linewidth=2)
        ax.fill_between([i - 0.2, i + 0.2],
                        [m - sd, m - sd],
                        [m + sd, m + sd],
                        alpha=0.15)
        ax.errorbar([i], [m], yerr=[sd], fmt="o", capsize=6)
        ax.hlines(med, i - 0.15, i + 0.15, linestyles="--", linewidth=1)
        ax.hlines(amin, i - 0.1, i + 0.1, linewidth=1)
        ax.hlines(amax, i - 0.1, i + 0.1, linewidth=1)

        local_range = max(amax - amin, 1e-6)
        y_text = amax + 0.05 * local_range
        text = f"μ={m:.2f}\nσ={sd:.2f}\nmin={amin:.2f}\nmax={amax:.2f}"
        ax.text(i, y_text, text, ha="center", va="bottom", fontsize=7)

    if np.isfinite(global_min) and np.isfinite(global_max):
        yr = max(global_max - global_min, 1e-6)
        ax.set_ylim(global_min - 0.05 * yr, global_max + 0.35 * yr)

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_xlabel("intra_op_num_threads")
    ax.set_ylabel("Inference time (ms)")
    ax.set_title("ONNX Runtime inference time vs intra_op_num_threads (pooled across runs)")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(VIOLIN_PNG_PATH, dpi=200)
    plt.close(fig)
    print("[INFO] Violin plot saved to:", VIOLIN_PNG_PATH)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  RUN  : onnx_threads_benchmark.py run <model.onnx> <images_dir> <threads> <run_id>")
        print("  PLOT : onnx_threads_benchmark.py plot")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "run":
        if len(sys.argv) != 6:
            print("Usage (run mode):")
            print("  onnx_threads_benchmark.py run <model.onnx> <images_dir> <threads> <run_id>")
            sys.exit(1)
        model_path = sys.argv[2]
        images_dir = sys.argv[3]
        threads = int(sys.argv[4])
        run_id = int(sys.argv[5])
        run_single_config(model_path, images_dir, threads, run_id)

    elif mode == "plot":
        plot_violin()

    else:
        print("[ERROR] Unknown mode:", mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
