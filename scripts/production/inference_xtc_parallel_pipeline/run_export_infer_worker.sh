#!/bin/bash
#SBATCH --partition=ada
#SBATCH --account=lcls:prjatomicspi19
#SBATCH --job-name=export_infer_worker
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus=1
#SBATCH --time=04:00:00
#SBATCH --output=logs_export/export_infer_worker_%j.out
#SBATCH --error=logs_export/export_infer_worker_%j.err

set -euo pipefail
# Python environment and script paths
PSCONDA_SH="/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh"

#YOLO's conda environment with PyTorch and dependencies for inference, has to be build in lcls-tools
YOLO_PYTHON="/sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/bin/python"

# Defaults (overridden via args)
RUN_NUMBER=146
EXP_NUMBER="mfx101232725"
MAX_EVENTS=400
PART_INDEX=0
CAMERA_NAME="inline_alvium"
TIMESTAMP_FILE=""
ORIGINAL_TIMESTAMP_FILE=""

for arg in "$@"; do
    case $arg in
        RUN_NUMBER=*) RUN_NUMBER="${arg#*=}" ;;
        EXP_NUMBER=*) EXP_NUMBER="${arg#*=}" ;;
        MAX_EVENTS=*) MAX_EVENTS="${arg#*=}" ;;
        PART_INDEX=*) PART_INDEX="${arg#*=}" ;;
        TIMESTAMP_FILE=*) TIMESTAMP_FILE="${arg#*=}" ;;
        ORIGINAL_TIMESTAMP_FILE=*) ORIGINAL_TIMESTAMP_FILE="${arg#*=}" ;;
        CAMERA_NAME=*) CAMERA_NAME="${arg#*=}" ;;
        *) echo "[WARN] Unknown argument: $arg" ;;
    esac
done

echo "[WORKER ${PART_INDEX}] run=${RUN_NUMBER} exp=${EXP_NUMBER} timestamps=${TIMESTAMP_FILE} original=${ORIGINAL_TIMESTAMP_FILE}"

echo "[WORKER ${PART_INDEX}] Starting in: $(pwd)"
WORKER_START=$(date +%s.%N)

set +u
source "${PSCONDA_SH}"
set -u

# Run export for this part (script is two levels up)
echo "[WORKER ${PART_INDEX}] === EXPORT PHASE START ==="
EXPORT_START=$(date +%s.%N)
python ../../export_xtc_segmented_timestamps.py ${RUN_NUMBER} ${EXP_NUMBER} ${MAX_EVENTS} "${CAMERA_NAME}" "${TIMESTAMP_FILE}" "${ORIGINAL_TIMESTAMP_FILE}"
EXPORT_END=$(date +%s.%N)
EXPORT_DURATION=$(echo "$EXPORT_END - $EXPORT_START" | bc -l)
echo "[WORKER ${PART_INDEX}] === EXPORT PHASE END (${EXPORT_DURATION} seconds) ==="

# export script created directories under current working dir; norm dir is named run_${RUN}_png_norm
IMG_DIR="run_${RUN_NUMBER}_png_norm"
if [ ! -d "${IMG_DIR}" ]; then
    echo "[WORKER ${PART_INDEX}] No image dir found: ${IMG_DIR}" >&2
    exit 1
fi

NUM_IMAGES=$(find "${IMG_DIR}" -name "*.png" | wc -l)
if [ ${NUM_IMAGES} -gt 0 ]; then
    EXPORT_PER_IMAGE=$(echo "$EXPORT_DURATION / $NUM_IMAGES" | bc -l)
    echo "[WORKER ${PART_INDEX}] Export: ${NUM_IMAGES} images in ${EXPORT_DURATION} sec (${EXPORT_PER_IMAGE} sec/image)"
fi

echo "[WORKER ${PART_INDEX}] === INFERENCE PHASE START ==="
INFER_START=$(date +%s.%N)
"${YOLO_PYTHON}" ../../inference_coyote_xtc.py "${IMG_DIR}"
INFER_END=$(date +%s.%N)
INFER_DURATION=$(echo "$INFER_END - $INFER_START" | bc -l)
echo "[WORKER ${PART_INDEX}] === INFERENCE PHASE END (${INFER_DURATION} seconds) ==="

if [ ${NUM_IMAGES} -gt 0 ]; then
    INFER_PER_IMAGE=$(echo "$INFER_DURATION / $NUM_IMAGES" | bc -l)
    echo "[WORKER ${PART_INDEX}] Inference: ${NUM_IMAGES} images in ${INFER_DURATION} sec (${INFER_PER_IMAGE} sec/image)"
fi

echo "[WORKER ${PART_INDEX}] Moving results to top-level results_csv_part_${PART_INDEX}"
mkdir -p ../results_csv_part_${PART_INDEX}

# event_data.csv is saved in run_<run>_png/event_data.csv relative to this CWD
if [ -f "run_${RUN_NUMBER}_png/event_data.csv" ]; then
    cp "run_${RUN_NUMBER}_png/event_data.csv" ../results_csv_part_${PART_INDEX}/event_data.csv
else
    echo "[WORKER ${PART_INDEX}] WARNING: event_data.csv not found" >&2
fi

# Copy inference CSVs from results_csv produced by inference
if [ -d "results_csv" ]; then
    for f in measurements_complete.csv measurements_above_threshold.csv; do
        if [ -f "results_csv/${f}" ]; then
            cp "results_csv/${f}" ../results_csv_part_${PART_INDEX}/${f}
        fi
    done
fi

WORKER_END=$(date +%s.%N)
WORKER_TOTAL=$(echo "$WORKER_END - $WORKER_START" | bc -l)

echo "[WORKER ${PART_INDEX}] ====== TIMING SUMMARY ======"
echo "[WORKER ${PART_INDEX}] Total time: ${WORKER_TOTAL} sec"
echo "[WORKER ${PART_INDEX}] Export:     ${EXPORT_DURATION} sec"
echo "[WORKER ${PART_INDEX}] Inference:  ${INFER_DURATION} sec"
if [ ${NUM_IMAGES} -gt 0 ]; then
    echo "[WORKER ${PART_INDEX}] Per image:  ${EXPORT_PER_IMAGE} sec (export) + ${INFER_PER_IMAGE} sec (inference)"
fi
echo "[WORKER ${PART_INDEX}] ============================"

echo "[WORKER ${PART_INDEX}] Done. Results at: $(pwd)/../results_csv_part_${PART_INDEX}"
