#!/bin/bash
#SBATCH --partition=turing
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=export_infer_xtc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus=1
#SBATCH --time=04:00:00
#SBATCH --output=logs_export/export_infer_turing_%j.out
#SBATCH --error=logs_export/export_infer_turing_%j.err

set -euo pipefail

export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID

echo "[SLURM] Host: $(hostname)"
echo "[SLURM] CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-"(not set)"}"
echo "[SLURM] Starting job..."

PSCONDA_SH="/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh"
YOLO_PYTHON="/sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/bin/python"

# -------  DEFAULT INPUTS ---------
RUN_NUMBER=61
EXP_NUMBER="mfx101346325"
SAVE_NORMALIZED=1
MAX_EVENTS=10000
USE_NORMALIZED=1
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
        USE_NORMALIZED=*)
            USE_NORMALIZED="${arg#*=}"
            ;;
        *)
            echo "[WARN] Unknown argument: $arg"
            ;;
    esac
done

echo "[ARGS] run=${RUN_NUMBER} exp=${EXP_NUMBER} save_norm=${SAVE_NORMALIZED} max_events=${MAX_EVENTS} use_normalized=${USE_NORMALIZED}"
echo

# ====================================
# NEW STEP 0: Create run folder and cd into it
# ====================================
RUN_DIR="run_${RUN_NUMBER}"
mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

echo "[STEP 0/3] Created and entered: $(pwd)"
echo

# ====================================
# STEP 1: Export XTC Data
# ====================================
echo "[STEP 1/3] Running export_xtc_normalized_args.py"
set +u
source "${PSCONDA_SH}"
set -u

# run from parent directory (scripts live one level up)
python ../export_xtc_normalized_args.py "${RUN_NUMBER}" "${EXP_NUMBER}" "${SAVE_NORMALIZED}" "${MAX_EVENTS}"

echo "[STEP 1/3] Export completed."
echo

# ====================================
# STEP 2: Run YOLO Inference
# ====================================
echo "[STEP 2/3] Running inference_coyote_xtc.py"

# Determine which image directory to use (now relative to run_${RUN_NUMBER}/)
if [ "${USE_NORMALIZED}" = "1" ]; then
    IMAGE_DIR="run_${RUN_NUMBER}_png_norm"
else
    IMAGE_DIR="run_${RUN_NUMBER}_png"
fi

"${YOLO_PYTHON}" ../inference_coyote_xtc.py "${IMAGE_DIR}"

echo "[STEP 2/3] Inference completed."
echo

# ====================================
# STEP 3: Merge Results
# ====================================
echo "[STEP 3/3] Running merge_crystals_data.py"
"${YOLO_PYTHON}" ../merge_crystals_data.py "${RUN_NUMBER}"

echo "[STEP 3/3] Merging completed."
echo

echo "[SLURM] Complete workflow finished successfully."
echo "Results saved to: ${RUN_DIR}/results_csv/"
