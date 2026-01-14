#!/bin/bash

#Default username
USER="pmonteil"

# ----------------------------
# Parse user namearguments
# ----------------------------
for arg in "$@"; do
  case $arg in
    --user=*)
      USER="${arg#*=}"
      shift
      ;;
    *)
      ;;
  esac
done


DEST_HOST="psana.sdf.slac.stanford.edu"

# Source images on psdev (CDS mount)
SOURCE_PATH="/cds/data/iocData/ioc-icl-alvium05/logs"

# Base folder on S3DF where runs are created
DEST_BASE="/sdf/data/lcls/ds/prj/prjlumine22/results/pmonteil/coyote_beamtime_19jan"

# Where you want results copied back on CDS
RESULTS_BACK_BASE="/cds/home/p/pmonteil"

echo "[INFO] Source images      : ${SOURCE_PATH}"
echo "[INFO] Remote base        : ${DEST_HOST}:${DEST_BASE}"
echo "[INFO] Results back to    : ${RESULTS_BACK_BASE}"
echo

# ------------------------------------------------------------
# 1) Create a new detection_N/images folder on psana
# ------------------------------------------------------------
RUN_DIR="$(ssh "${USER}@${DEST_HOST}" "bash -lc '
  set -euo pipefail
  mkdir -p \"${DEST_BASE}\"

  i=1
  while [ -d \"${DEST_BASE}/detection_\$i\" ]; do
    i=\$((i+1))
  done

  RUN=\"${DEST_BASE}/detection_\$i\"
  mkdir -p \"\$RUN/images\"
  echo \"\$RUN\"
'")"

echo "[INFO] Created remote run dir: ${RUN_DIR}"

# ------------------------------------------------------------
# 2) Copy images into detection_N/images/
# ------------------------------------------------------------
echo "[INFO] Copying images to ${RUN_DIR}/images/ ..."
rsync -avr --delete \
  "${SOURCE_PATH}/" \
  "${USER}@${DEST_HOST}:${RUN_DIR}/images/"

# ------------------------------------------------------------
# 3) Launch run_inference.sh from inside detection_N
#    Assumption: run_inference.sh exists on psana at ../RUN_DIR/run_inference.sh
#    If it lives elsewhere, see note below.
# ------------------------------------------------------------
echo "[INFO] Launching inference job..."
JOB_ID="$(ssh "${USER}@${DEST_HOST}" "bash -lc '
  set -euo pipefail
  cd \"${RUN_DIR}\"
  jid=\$(sbatch --parsable ../run_inference.sh)
  echo \$jid
'")"

echo "[INFO] Submitted job: ${JOB_ID}"

# ------------------------------------------------------------
# 4) Wait for CSV output
# ------------------------------------------------------------
REMOTE_CSV="${RUN_DIR}/runs/size_measurements/measurements_complete.csv"
echo "[INFO] Waiting for output CSV: ${REMOTE_CSV}"

while true; do
  if ssh "${USER}@${DEST_HOST}" "bash -lc 'test -f \"${REMOTE_CSV}\"'"; then
    echo "[INFO] CSV detected."
    break
  fi
  sleep 0.5
done

# ------------------------------------------------------------
# 5) Copy results back to CDS
# ------------------------------------------------------------
RUN_NAME="$(basename "${RUN_DIR}")"
LOCAL_DEST_DIR="${RESULTS_BACK_BASE}/${RUN_NAME}"
mkdir -p "${LOCAL_DEST_DIR}"

echo "[INFO] Copying CSV back to: ${LOCAL_DEST_DIR}/"
rsync -avr \
  "${USER}@${DEST_HOST}:${REMOTE_CSV}" \
  "${LOCAL_DEST_DIR}/"

echo
echo "[DONE] Results available at:"
echo "       ${LOCAL_DEST_DIR}/measurements_complete.csv"

