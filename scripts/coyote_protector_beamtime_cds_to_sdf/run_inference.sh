#!/bin/bash
#SBATCH --partition=turing
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=yolo_detection
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4                 # CPU mostly for I/O + Python
#SBATCH --gpus=1                       # request 1 GPU
#SBATCH --time=04:00:00
#SBATCH --output=logs_detection/detection_turing_%j.out
#SBATCH --error=logs_detection/detection_turing_%j.err

# ==== Thread / OMP hygiene ====
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

# ==== CUDA visibility for multi-GPU ====
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0,1,2,3

echo "[SLURM] Allocated GPUs: $CUDA_VISIBLE_DEVICES"

echo "[SLURM] Running inference_coyote.py on $(hostname)"

# /sdf/home/p/pmonteil/miniconda3/envs/coyote/bin/python ../inference_coyote.py

/sdf/data/lcls/ds/prj/prjlumine22/results/coyote_protector/miniconda3_coyote/envs/env_coyote/bin/python ../inference_coyote.py
