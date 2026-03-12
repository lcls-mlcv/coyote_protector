# Must source this env before running:
# source /sdf/group/lcls/ds/ana/sw/conda2/manage/bin/psconda.sh

import sys
import json
import os
from psana import DataSource
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Configure psana parallelization via environment
# (only needed if running with mpirun; will be ignored if running serially)
os.environ['PS_EB_NODES'] = '1'   # event builders (default is 1)
os.environ['PS_SRV_NODES'] = '1'  # output/gathering nodes


# -------------------------
# Argument parsing
# -------------------------
DEFAULT_RUN = 146
DEFAULT_EXP = "mfx101232725"
DEFAULT_MAX_EVENTS = 100

argc = len(sys.argv)

if argc == 1:
    run_number = DEFAULT_RUN
    exp = DEFAULT_EXP
    max_events = DEFAULT_MAX_EVENTS
elif argc in (2, 3, 4):
    run_number = int(sys.argv[1])
    exp = sys.argv[2] if argc >= 3 else DEFAULT_EXP
    max_events = int(sys.argv[3]) if argc >= 4 else DEFAULT_MAX_EVENTS
else:
    print(
        "Usage:\n"
        "  python export_xtc_timestamps.py\n"
        "  python export_xtc_timestamps.py <run_number>\n"
        "  python export_xtc_timestamps.py <run_number> <exp_number>\n"
        "  python export_xtc_timestamps.py <run_number> <exp_number> <max_events>\n"
    )
    sys.exit(1)

print(f"[CONFIG] exp={exp} run={run_number} max_events={max_events}")

# -------------------------
# psana setup
# -------------------------
ds = DataSource(exp=exp, run=[run_number], max_events=max_events)

myrun = next(ds.runs())
# -------------------------
# Event loop
# -------------------------
timestamps = []

for evt in myrun.events():
    timestamps.append(evt.timestamp)

# Only rank 0 writes to avoid file conflicts
if rank == 0:
    # Check if timestamps are in order
    timestamps_sorted = sorted(timestamps)
    is_sorted = (timestamps == timestamps_sorted)
    
    if not is_sorted:
        print(f"[WARNING] Timestamps are NOT in ascending order!")
        print(f"[INFO] Sorting {len(timestamps)} timestamps...")
    else:
        print(f"[INFO] Timestamps are already in ascending order")
    
    # Save sorted timestamps
    with open(f"timestamps_run_{run_number}.json", "w") as f:
        json.dump(timestamps_sorted, f)
    
    print(f"[INFO] Collected {len(timestamps)} timestamps and saved to timestamps_run_{run_number}.json")
