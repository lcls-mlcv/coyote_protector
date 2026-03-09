#!/bin/bash
#SBATCH --partition=milano
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=yolo_benchmark
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs_benchmark/benchmark_%j.out
#SBATCH --error=logs_benchmark/benchmark_%j.err
#SBATCH --exclusive

# ==== Thread / OMP hygiene ====
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

echo "[SLURM] Running benchmark_models.py on $(hostname)"
python benchmark_models.py
