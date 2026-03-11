#!/bin/bash
#
# routine_detection_v3.sh
# Orchestrates the XTC export and inference workflow
# Runs on CDS and launches export_infer_xtc.sh on SDF via SSH
#

# -------  DEFAULT INPUTS ---------
USER="pmonteil"
RUN_NUMBER=146
EXP_NUMBER="mfx101232725"
SAVE_NORMALIZED=1
MAX_EVENTS=400
USE_NORMALIZED=1
NUM_PARTS=4
CAMERA_NAME="inline_alvium"
# --------------------------------

DEST_HOST="psana.sdf.slac.stanford.edu"
SDF_BASE="/sdf/data/lcls/ds/mfx/exp_id/results/your/folder/to/process/"  # <-- UPDATE THIS PATH TO YOUR SDF WORKING DIRECTORY
RESULTS_BACK_BASE="path/to/results_back_on_cds"  # <-- UPDATE THIS PATH TO YOUR LOCAL RESULTS DIRECTORY

# -------  PARSE key=value arguments ---------
for arg in "$@"; do
    case $arg in
        --user=*)
            USER="${arg#*=}"
            ;;
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
        NUM_PARTS=*)
            NUM_PARTS="${arg#*=}"
            ;;
        CAMERA_NAME=*)
            CAMERA_NAME="${arg#*=}"
            ;;
        *)
            echo "[WARN] Unknown argument: $arg"
            ;;
    esac
done

echo "[INFO] =============================================="
echo "[INFO] COYOTE PROTECTOR XTC DETECTION ROUTINE v3"
echo "[INFO] =============================================="
echo "[INFO] User: ${USER}"
echo "[INFO] SDF Host: ${DEST_HOST}"
echo "[INFO] SDF Base: ${SDF_BASE}"
echo "[INFO] Run Number: ${RUN_NUMBER}"
echo "[INFO] Experiment: ${EXP_NUMBER}"
echo "[INFO] Save Normalized: ${SAVE_NORMALIZED}"
echo "[INFO] Max Events: ${MAX_EVENTS}"
echo "[INFO] Use Normalized for Inference: ${USE_NORMALIZED}"
echo "[INFO] Number of Parts: ${NUM_PARTS}"
echo "[INFO] Camera Name: ${CAMERA_NAME}"
echo "[INFO] Results back to: ${RESULTS_BACK_BASE}"
echo

# ====================================
# STEP 1: Launch export_infer_xtc.sh on SDF via SSH
# ====================================
echo "[STEP 1/3] Launching export_infer_xtc_paralled.sh on SDF..."

JOB_ID="$(ssh "${USER}@${DEST_HOST}" "bash -lc '
  set -euo pipefail
  cd \"${SDF_BASE}\"
        jid=\$(sbatch --parsable run_export_infer_xtc_parallel.sh RUN_NUMBER=${RUN_NUMBER} EXP_NUMBER=${EXP_NUMBER} MAX_EVENTS=${MAX_EVENTS} NUM_PARTS=${NUM_PARTS} CAMERA_NAME=${CAMERA_NAME})
  echo \$jid
'")"

echo "[INFO] Submitted job on SDF: ${JOB_ID}"
echo

# ====================================
# STEP 2: Wait for results on SDF
# ====================================
echo "[STEP 2/3] Waiting for merged results on SDF..."

REMOTE_CSV="${SDF_BASE}/run_${RUN_NUMBER}/results_csv/merged_crystals.csv"

max_attempts=360  # 3 hours with 30-second intervals
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if ssh "${USER}@${DEST_HOST}" "bash -lc 'test -f \"${REMOTE_CSV}\"'"; then
        echo "[INFO] Merged CSV detected on SDF."
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 4)) -eq 0 ]; then
        echo "[INFO] Waiting... (attempt $attempt/$max_attempts)"
    fi
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "[ERROR] Timeout waiting for results after 3 hours"
    exit 1
fi

echo

# ====================================
# STEP 3: Copy all results back to CDS
# ====================================
echo "[STEP 3/3] Copying results back to CDS..."

RESULTS_DIR="run_${RUN_NUMBER}_results"
LOCAL_DEST_DIR="${RESULTS_BACK_BASE}/${RESULTS_DIR}"
mkdir -p "${LOCAL_DEST_DIR}"

echo "[INFO] Copying from: ${DEST_HOST}:${SDF_BASE}/run_${RUN_NUMBER}/results_csv/"
echo "[INFO] Copying to: ${LOCAL_DEST_DIR}/"

rsync -avr \
  "${USER}@${DEST_HOST}:${SDF_BASE}/run_${RUN_NUMBER}/results_csv/" \
  "${LOCAL_DEST_DIR}/"

echo
echo "[DONE] =============================================="
echo "[INFO] Complete workflow finished successfully."
echo "[INFO] Results available at:"
echo "[INFO]   ${LOCAL_DEST_DIR}/"
echo "[INFO] =============================================="
echo "[INFO] Key files:"
echo "[INFO]   - merged_crystals.csv          (all data merged)"
echo "[INFO]   - measurements_complete.csv    (all detections)"
echo "[INFO]   - measurements_above_threshold_complete.csv (above threshold only)"
echo "[INFO]   - event_data.csv               (trajectory data)"
echo "[DONE]"
