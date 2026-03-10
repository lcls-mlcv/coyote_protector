#!/bin/bash
#SBATCH --partition=turing
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=yolo_benchmark
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4                 # CPU mostly for I/O + Python
#SBATCH --gpus=1                       # request 1 GPU
#SBATCH --time=04:00:00
#SBATCH --output=logs_benchmark/benchmark_turing_%j.out
#SBATCH --error=logs_benchmark/benchmark_turing_%j.err

# ==== Thread / OMP hygiene ====
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

# ==== CUDA visibility for multi-GPU ====
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0

echo "[SLURM] Allocated GPUs: $CUDA_VISIBLE_DEVICES"

# ==== Go to models folder and run benchmark ====
cd /sdf/home/p/pmonteil/coyote_protector/models
mkdir -p logs_benchmark

echo "[SLURM] Running benchmark.py on $(hostname)"
python benchmark.py
