#!/bin/bash
#SBATCH --partition=milano
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=onnx_threads_benchmark
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10        # >= max threads tested
#SBATCH --time=01:00:00
#SBATCH --output=logs_benchmark_onnx_threads/onnx_threads_%j.out
#SBATCH --error=logs_benchmark_onnx_threads/onnx_threads_%j.err
#SBATCH --exclusive

set -euo pipefail
mkdir -p logs_benchmark_onnx_threads

echo "[SLURM] Job ID      : $SLURM_JOB_ID"
echo "[SLURM] Node list   : $SLURM_NODELIST"
echo "[SLURM] CPUs/task   : $SLURM_CPUS_PER_TASK"

# ============================================================
# 1) Threading limits (BLAS / OpenMP)
# ============================================================
export OMP_PROC_BIND=close
export OMP_PLACES=cores

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export NUMEXPR_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export VECLIB_MAXIMUM_THREADS="${SLURM_CPUS_PER_TASK}"

echo "[ENV] OMP_NUM_THREADS=$OMP_NUM_THREADS"
echo "[ENV] MKL_NUM_THREADS=$MKL_NUM_THREADS"
echo "[ENV] OPENBLAS_NUM_THREADS=$OPENBLAS_NUM_THREADS"
echo "[ENV] NUMEXPR_NUM_THREADS=$NUMEXPR_NUM_THREADS"
echo "[ENV] VECLIB_MAXIMUM_THREADS=$VECLIB_MAXIMUM_THREADS"

# ============================================================
# 2) Paths (edit as needed)
# ============================================================
MODEL="/sdf/home/p/pmonteil/optimization_cpp/model_export_optim/best_prak_v8.onnx"
SRC_IMG_DIR="/sdf/home/p/pmonteil/coyote_protector_test_PL_4/chip_pic_prakriti"
SCRIPT_DIR="/sdf/home/p/pmonteil/coyote_protector_benchmark/scripts"

SCRIPT_PY="onnx_threads_benchmark.py"

if [[ ! -f "${MODEL}" ]]; then
    echo "[ERROR] Model not found: ${MODEL}"
    exit 1
fi
if [[ ! -d "${SRC_IMG_DIR}" ]]; then
    echo "[ERROR] Image dir not found: ${SRC_IMG_DIR}"
    exit 1
fi
if [[ ! -f "${SCRIPT_DIR}/${SCRIPT_PY}" ]]; then
    echo "[ERROR] Python script not found: ${SCRIPT_DIR}/${SCRIPT_PY}"
    exit 1
fi

# ============================================================
# 3) Optional: copy images to local scratch
# ============================================================
if [[ -n "${SLURM_TMPDIR:-}" ]]; then
    echo "[I/O] Copying images to \$SLURM_TMPDIR for faster access"
    LOCAL_IMG_DIR="$SLURM_TMPDIR/chip_pic_prakriti"
    mkdir -p "$LOCAL_IMG_DIR"
    cp -r "${SRC_IMG_DIR}/" "$LOCAL_IMG_DIR/"
    IMAGES="$LOCAL_IMG_DIR"
else
    echo "[I/O] SLURM_TMPDIR not set; using original path"
    IMAGES="$SRC_IMG_DIR"
fi

echo "[INFO] Using model : ${MODEL}"
echo "[INFO] Using images: ${IMAGES}"

cd "${SCRIPT_DIR}"

# ============================================================
# 4) Configs to test (intra_op_num_threads) and runs per config
# ============================================================
THREADS_LIST=(1 2 4 6 8 10)
RUNS=10   # number of runs per configuration

BENCH_DIR="benchmark_cpu_onnx_threads"
mkdir -p "${BENCH_DIR}"

CPU_SUMMARY_CSV="${BENCH_DIR}/cpu_usage_summary.csv"
if [[ ! -f "${CPU_SUMMARY_CSV}" ]]; then
    echo "config_threads,run_id,max_cpu_pct,approx_cores" > "${CPU_SUMMARY_CSV}"
fi

# ============================================================
# 5) Loop over configurations and runs
# ============================================================
for T in "${THREADS_LIST[@]}"; do
  for RUN in $(seq 1 "${RUNS}"); do
    echo
    echo "====================================="
    echo "[RUN] Configuration: intra_op_num_threads=${T}, run_id=${RUN}"
    echo "====================================="

    PIDSTAT_LOG="logs_benchmark_onnx_threads/pidstat_threads${T}_run${RUN}_job${SLURM_JOB_ID}.log"
    echo "[MONITOR] Starting pidstat -> ${PIDSTAT_LOG}"

    # Start pidstat (CPU/RAM/I/O/threads) at 1s interval
    pidstat -dlrut 1 > "${PIDSTAT_LOG}" &
    PIDSTAT_PID=$!

    cleanup_cfg() {
        echo "[MONITOR] Stopping pidstat (PID=${PIDSTAT_PID}) for T=${T}, run_id=${RUN}"
        kill "${PIDSTAT_PID}" 2>/dev/null || true
    }

    # Ensure pidstat is killed even if python crashes
    trap cleanup_cfg EXIT

    # --- Run Python benchmark for this config+run ---
    echo "[RUN] python3 ${SCRIPT_PY} run \"${MODEL}\" \"${IMAGES}\" ${T} ${RUN}"
    time python3 "${SCRIPT_PY}" run "${MODEL}" "${IMAGES}" "${T}" "${RUN}"

    # Stop pidstat for this config+run
    cleanup_cfg
    # Remove trap so it does not fire twice in next loop
    trap - EXIT

    echo "[ANALYSIS] Parsing pidstat log to estimate CPU usage for T=${T}, run_id=${RUN}"

    if [[ -f "${PIDSTAT_LOG}" ]]; then
        # Find max %CPU used by python(3) running onnx_threads_benchmark.py run ...
        MAX_CPU_PCT=$(awk '
            ($12=="python" || $12=="python3") && $13=="onnx_threads_benchmark.py" && $14=="run" && $10 ~ /^[0-9.]+$/ {
                if ($10 + 0 > max) max = $10 + 0
            }
            END {
                if (max == 0) print 0; else print max;
            }
        ' "${PIDSTAT_LOG}")

        MAX_CORES=$(awk -v m="${MAX_CPU_PCT}" 'BEGIN { if (m==0) print 0; else printf "%.2f", m/100.0 }')

        echo "[ANALYSIS] T=${T}, run_id=${RUN} → Max %CPU: ${MAX_CPU_PCT}%, approx cores: ${MAX_CORES}"
        echo "${T},${RUN},${MAX_CPU_PCT},${MAX_CORES}" >> "${CPU_SUMMARY_CSV}"
    else
        echo "[WARN] pidstat log not found for T=${T}, run_id=${RUN}, skipping CPU analysis."
    fi

  done
done

# ============================================================
# 6) Generate cpu_usage.txt (human-readable summary)
# ============================================================
CPU_USAGE_TXT="${BENCH_DIR}/cpu_usage.txt"
if [[ -f "${CPU_SUMMARY_CSV}" ]]; then
    echo "[INFO] Generating ${CPU_USAGE_TXT} from ${CPU_SUMMARY_CSV}"
    awk -F, 'NR>1 {
        printf "threads=%s run_id=%s : max_cpu_pct=%s approx_cores=%s\n", $1, $2, $3, $4
    }' "${CPU_SUMMARY_CSV}" > "${CPU_USAGE_TXT}"
else
    echo "[WARN] ${CPU_SUMMARY_CSV} not found, cannot create cpu_usage.txt"
fi

# ============================================================
# 7) Generate violin plot from all configs (pooled across runs)
# ============================================================
echo
echo "[PLOT] Generating violin plot from benchmark_cpu_onnx_threads/onnx_infer_times.csv"
python3 "${SCRIPT_PY}" plot

echo
echo "[DONE] All configurations tested."
echo "[INFO] Inference times CSV  : ${BENCH_DIR}/onnx_infer_times.csv"
echo "[INFO] Config summary CSV   : ${BENCH_DIR}/onnx_infer_summary_per_config.csv"
echo "[INFO] CPU usage summary    : ${CPU_SUMMARY_CSV}"
echo "[INFO] CPU usage text       : ${CPU_USAGE_TXT}"
echo "[INFO] Violin plot          : ${BENCH_DIR}/violin_infer_time_by_threads.png"
