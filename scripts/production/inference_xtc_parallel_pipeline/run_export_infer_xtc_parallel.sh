#!/bin/bash
#SBATCH --partition=milano
#SBATCH --account=lcls:prjlumine22
#SBATCH --job-name=export_infer_xtc_parallel
#SBATCH --ntasks=50
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --gpus=0
#SBATCH --time=02:00:00
#SBATCH --output=logs_export/export_infer_parallel_%j.out
#SBATCH --error=logs_export/export_infer_parallel_%j.err

set -euo pipefail

export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-2}"

PSCONDA_SH="/sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh"

# -------  DEFAULT INPUTS ---------
RUN_NUMBER=146
EXP_NUMBER="mfx101232725"
MAX_EVENTS=400
NUM_PARTS=4
CAMERA_NAME="inline_alvium"
# --------------------------------

for arg in "$@"; do
    case $arg in
        RUN_NUMBER=*) RUN_NUMBER="${arg#*=}" ;;
        EXP_NUMBER=*) EXP_NUMBER="${arg#*=}" ;;
        MAX_EVENTS=*) MAX_EVENTS="${arg#*=}" ;;
        NUM_PARTS=*) NUM_PARTS="${arg#*=}" ;;
        CAMERA_NAME=*) CAMERA_NAME="${arg#*=}" ;;
        *) echo "[WARN] Unknown argument: $arg" ;;
    esac
done

echo "[MASTER] run=${RUN_NUMBER} exp=${EXP_NUMBER} max_events=${MAX_EVENTS} parts=${NUM_PARTS} camera=${CAMERA_NAME}"

MASTER_START=$(date +%s.%N)

# Create run dir and cd into it
RUN_DIR="run_${RUN_NUMBER}"
mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}"

echo "[MASTER] Created and entered: $(pwd)"

echo "[MASTER] Step 1: Export timestamps with 50 MPI processes"
TIMESTAMPS_START=$(date +%s.%N)
set +u
source "${PSCONDA_SH}"
set -u

# run timestamps exporter with 50 MPI processes (psana distributes events across ranks)
python ../export_xtc_timestamps.py ${RUN_NUMBER} ${EXP_NUMBER} ${MAX_EVENTS}
TIMESTAMPS_END=$(date +%s.%N)
TIMESTAMPS_DURATION=$(echo "$TIMESTAMPS_END - $TIMESTAMPS_START" | bc -l)
echo "[MASTER] Timestamps export time: ${TIMESTAMPS_DURATION} sec"

TS_JSON="timestamps_run_${RUN_NUMBER}.json"
if [ ! -f "${TS_JSON}" ]; then
    echo "[ERROR] timestamps JSON not created: ${TS_JSON}"
    exit 1
fi

echo "[MASTER] Splitting timestamps into ${NUM_PARTS} parts"
SPLIT_START=$(date +%s.%N)
mkdir -p timestamps_parts
python3 ../split_timestamps.py "${TS_JSON}" ${NUM_PARTS} timestamps_parts
SPLIT_END=$(date +%s.%N)
SPLIT_DURATION=$(echo "$SPLIT_END - $SPLIT_START" | bc -l)
echo "[MASTER] Timestamps splitting time: ${SPLIT_DURATION} sec"

echo "[MASTER] Submitting ${NUM_PARTS} worker jobs"
WORKER_IDS=()
ORIGINAL_TS_FILE="$(pwd)/${TS_JSON}"
for i in $(seq 0 $((NUM_PARTS-1))); do
    PART_DIR="part_${i}"
    mkdir -p "${PART_DIR}"
    TIMESTAMP_FILE="$(pwd)/timestamps_parts/timestamps_part_${i}.json"
    jid=$(sbatch --parsable --chdir=$(pwd)/${PART_DIR} ../run_export_infer_worker.sh RUN_NUMBER=${RUN_NUMBER} EXP_NUMBER=${EXP_NUMBER} MAX_EVENTS=${MAX_EVENTS} PART_INDEX=${i} CAMERA_NAME=${CAMERA_NAME} TIMESTAMP_FILE=${TIMESTAMP_FILE} ORIGINAL_TIMESTAMP_FILE=${ORIGINAL_TS_FILE})
    echo "[MASTER] Submitted worker ${i} → job ${jid}"
    WORKER_IDS+=("${jid}")
done

echo "[MASTER] Waiting for workers to produce their results..."
RESULTS_DIR="results_csv"
mkdir -p "${RESULTS_DIR}"

WAIT_START=$(date +%s.%N)
max_attempts=720  # allow up to 6 hours
attempt=0
while [ $attempt -lt $max_attempts ]; do
    ready=0
    for i in $(seq 0 $((NUM_PARTS-1))); do
        if [ -f "results_csv_part_${i}/measurements_complete.csv" ] && [ -f "results_csv_part_${i}/event_data.csv" ]; then
            ready=$((ready+1))
        fi
    done
    if [ "$ready" -eq "${NUM_PARTS}" ]; then
        echo "[MASTER] All ${NUM_PARTS} worker results present"
        break
    fi
    attempt=$((attempt+1))
    if [ $((attempt % 6)) -eq 0 ]; then
        echo "[MASTER] Waiting... (attempt $attempt/$max_attempts)"
    fi
    sleep 30
done
WAIT_END=$(date +%s.%N)
WAIT_DURATION=$(echo "$WAIT_END - $WAIT_START" | bc -l)

if [ $attempt -eq $max_attempts ]; then
    echo "[ERROR] Timeout waiting for worker results"
    exit 1
fi

echo "[MASTER] Worker wait time: ${WAIT_DURATION} sec"

echo "[MASTER] Merging part CSVs into ${RESULTS_DIR}"
MERGE_START=$(date +%s.%N)
mkdir -p "${RESULTS_DIR}"

# Merge event_data.csv (preserve header from first file)
first=1
for i in $(seq 0 $((NUM_PARTS-1))); do
    part_event="results_csv_part_${i}/event_data.csv"
    if [ ! -f "${part_event}" ]; then
        echo "[WARN] Missing ${part_event}, skipping"
        continue
    fi
    if [ $first -eq 1 ]; then
        cp "${part_event}" "${RESULTS_DIR}/event_data.csv"
        first=0
    else
        tail -n +2 "${part_event}" >> "${RESULTS_DIR}/event_data.csv"
    fi
done

# Merge measurements_complete.csv
first=1
for i in $(seq 0 $((NUM_PARTS-1))); do
    part_meas="results_csv_part_${i}/measurements_complete.csv"
    if [ ! -f "${part_meas}" ]; then
        echo "[WARN] Missing ${part_meas}, skipping"
        continue
    fi
    if [ $first -eq 1 ]; then
        cp "${part_meas}" "${RESULTS_DIR}/measurements_complete.csv"
        first=0
    else
        tail -n +2 "${part_meas}" >> "${RESULTS_DIR}/measurements_complete.csv"
    fi
done

# Merge measurements_above_threshold.csv
first=1
for i in $(seq 0 $((NUM_PARTS-1))); do
    part_meas="results_csv_part_${i}/measurements_above_threshold.csv"
    if [ ! -f "${part_meas}" ]; then
        echo "[WARN] Missing ${part_meas}, skipping"
        continue
    fi
    if [ $first -eq 1 ]; then
        cp "${part_meas}" "${RESULTS_DIR}/measurements_above_threshold.csv"
        first=0
    else
        tail -n +2 "${part_meas}" >> "${RESULTS_DIR}/measurements_above_threshold.csv"
    fi
done

echo "[MASTER] Running final merge_crystals_data.py"
python ../merge_crystals_data.py ${RUN_NUMBER}
MERGE_END=$(date +%s.%N)
MERGE_DURATION=$(echo "$MERGE_END - $MERGE_START" | bc -l)

MASTER_END=$(date +%s.%N)
MASTER_TOTAL=$(echo "$MASTER_END - $MASTER_START" | bc -l)

echo ""
echo "[MASTER] ====== MASTER JOB TIMING SUMMARY ======"
echo "[MASTER] Total workflow time: ${MASTER_TOTAL} sec"
echo "[MASTER] Timestamps export:   ${TIMESTAMPS_DURATION} sec"
echo "[MASTER] Timestamps split:    ${SPLIT_DURATION} sec"
echo "[MASTER] Waiting for workers: ${WAIT_DURATION} sec"
echo "[MASTER] CSV merge & final:   ${MERGE_DURATION} sec"
echo "[MASTER] ========================================="

echo "[MASTER] Done. Results in: $(pwd)/results_csv"
