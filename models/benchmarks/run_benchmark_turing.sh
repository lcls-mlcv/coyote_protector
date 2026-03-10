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

# ==== Determine paths and always anchor execution in models/benchmarks ====
SUBMIT_DIR="${SLURM_SUBMIT_DIR:-$PWD}"

if [[ -f "$SUBMIT_DIR/benchmark.py" ]]; then
	BENCHMARKS_DIR="$SUBMIT_DIR"
elif [[ -f "$SUBMIT_DIR/benchmarks/benchmark.py" ]]; then
	BENCHMARKS_DIR="$SUBMIT_DIR/benchmarks"
else
	echo "[ERROR] Could not locate benchmark.py from submit dir: $SUBMIT_DIR"
	echo "[ERROR] Expected one of:"
	echo "        $SUBMIT_DIR/benchmark.py"
	echo "        $SUBMIT_DIR/benchmarks/benchmark.py"
	exit 1
fi

# ==== Run inside benchmarks so all relative outputs stay there ====
cd "$BENCHMARKS_DIR"
mkdir -p "$BENCHMARKS_DIR/logs_benchmark"

echo "[SLURM] Running benchmark.py on $(hostname)"
echo "[SLURM] BENCHMARKS_DIR=$BENCHMARKS_DIR"

if command -v python3 >/dev/null 2>&1; then
	python3 "$BENCHMARKS_DIR/benchmark.py"
elif command -v python >/dev/null 2>&1; then
	python "$BENCHMARKS_DIR/benchmark.py"
else
	echo "[ERROR] Neither python3 nor python is available in PATH"
	exit 127
fi
