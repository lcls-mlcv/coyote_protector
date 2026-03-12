#!/bin/bash
#SBATCH --partition=turing
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=export_xtc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=logs_export/export_turing_%j.out
#SBATCH --error=logs_export/export_turing_%j.err

set -euo pipefail

export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

echo "[SLURM] Host: $(hostname)"
echo "[SLURM] Starting job..."

PSCONDA_SH="/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh"

# -------  DEFAULT INPUTS ---------
RUN_NUMBER=61
EXP_NUMBER="mfx101346325"
SAVE_NORMALIZED=1
MAX_EVENTS=10000
CAMERA_NAME="inline_alvium"
# --------------------------------

# -------  PARSE key=value arguments ---------
for arg in "$@"; do
    case $arg in
        RUN_NUMBER=*)
            RUN_NUMBER="${arg#*=}"
            ;;
        EXP_NUMBER=*)
            EXP_NUMBER="${arg#*=}"
            ;;
        SAVE_NORMALIZED=*)
            SAVE_NORMALIZED="${arg#*=}"
            ;;
        MAX_EVENTS=*)
            MAX_EVENTS="${arg#*=}"
            ;;
        CAMERA_NAME=*)
            CAMERA_NAME="${arg#*=}"
            ;;
        *)
            echo "[WARN] Unknown argument: $arg"
            ;;
    esac
done

echo "[ARGS] run=${RUN_NUMBER} exp=${EXP_NUMBER} save_norm=${SAVE_NORMALIZED} max_events=${MAX_EVENTS} camera=${CAMERA_NAME}"
echo

echo "[STEP 1/1] Running export_xtc_normalized_args.py"
START_EXPORT=$(date +%s.%N)
set +u
source "${PSCONDA_SH}"
set -u

python ./export_xtc_normalized_args.py "${RUN_NUMBER}" "${EXP_NUMBER}" "${SAVE_NORMALIZED}" "${MAX_EVENTS}" "${CAMERA_NAME}"
END_EXPORT=$(date +%s.%N)
DURATION_EXPORT=$(echo "$END_EXPORT - $START_EXPORT" | bc -l)

# Count the number of images processed
if [ "${SAVE_NORMALIZED}" = "1" ]; then
    IMAGE_DIR="run_${RUN_NUMBER}_png_norm"
else
    IMAGE_DIR="run_${RUN_NUMBER}_png"
fi
NUM_IMAGES=$(find "${IMAGE_DIR}" -name "*.png" | wc -l)

echo "[STEP 1/1] Export completed. Processed ${NUM_IMAGES} images."
echo

echo "[SLURM] Export completed successfully."
echo "=== TIMING PROFILE ==="
echo "Total images processed: ${NUM_IMAGES}"
echo "Export XTC Data: ${DURATION_EXPORT} seconds total, $(echo "$DURATION_EXPORT / $NUM_IMAGES" | bc -l) seconds per image"
