#!/bin/bash
#SBATCH --partition=turing
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=inference_xtc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus=1
#SBATCH --time=02:00:00
#SBATCH --output=logs_export/inference_turing_%j.out
#SBATCH --error=logs_export/inference_turing_%j.err

set -euo pipefail

export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID

echo "[SLURM] Host: $(hostname)"
echo "[SLURM] CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-"(not set)"}"
echo "[SLURM] Starting job..."

# -------  DEFAULT INPUTS ---------
RUN_NUMBER=61
USE_NORMALIZED=1
# --------------------------------

# -------  PARSE key=value arguments ---------
for arg in "$@"; do
    case $arg in
        RUN_NUMBER=*)
            RUN_NUMBER="${arg#*=}"
            ;;
        USE_NORMALIZED=*)
            USE_NORMALIZED="${arg#*=}"
            ;;
        *)
            echo "[WARN] Unknown argument: $arg"
            ;;
    esac
done

echo "[ARGS] run=${RUN_NUMBER} use_normalized=${USE_NORMALIZED}"
echo

# Determine which image directory to use
if [ "${USE_NORMALIZED}" = "1" ]; then
    IMAGE_DIR="run_${RUN_NUMBER}/run_${RUN_NUMBER}_png_norm"
else
    IMAGE_DIR="run_${RUN_NUMBER}/run_${RUN_NUMBER}_png"
fi

echo "[STEP 1/2] Running inference_coyote_xtc.py"
python ./inference_coyote_xtc.py "${IMAGE_DIR}"

echo
echo "[STEP 2/2] Running merge_crystals_data.py"
python ./merge_crystals_data.py "${RUN_NUMBER}"

echo
echo "[SLURM] Inference and merging completed successfully."
