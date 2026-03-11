#!/usr/bin/env python3
"""
bash_launcher.py
Launches routine_detection_v3.sh with specified arguments.
Can be run from CDS to orchestrate the complete XTC workflow.

USAGE:
    python bash_launcher.py [OPTIONS]
    python bash_launcher.py --help

EXAMPLES:
    # Run with defaults
    python bash_launcher.py

    # Run with custom parameters
    python bash_launcher.py --run_number=61 --exp_number=mfx101346325 --max_events=80000

    # Run with specific user
    python bash_launcher.py --user=pmonteil --run_number=100
"""

import argparse
import subprocess
import sys
from pathlib import Path


def eprint(msg):
    """Write message to stderr."""
    sys.stderr.write(str(msg) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Launch coyote XTC detection routine via bash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--user",
        default="pmonteil",
        help="Username for SSH to SDF (default: pmonteil)"
    )
    parser.add_argument(
        "--run_number",
        type=int,
        default=146,
        help="LCLS run number to process (default: 146)"
    )
    parser.add_argument(
        "--exp_number",
        default="mfx101232725",
        help="Experiment identifier (default: mfx101232725)"
    )
    parser.add_argument(
        "--save_normalized",
        type=int,
        choices=[0, 1],
        default=1,
        help="Save normalized images (1=yes, 0=no, default: 1)"
    )
    parser.add_argument(
        "--max_events",
        type=int,
        default=100,
        help="Maximum events to process (default: 100)"
    )
    parser.add_argument(
        "--use_normalized",
        type=int,
        choices=[0, 1],
        default=1,
        help="Use normalized images for inference (1=yes, 0=no, default: 1)"
    )
    parser.add_argument(
        "--num_parts",
        type=int,
        default=4,
        help="Number of parallel parts to divide the workflow (default: 4)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print command without executing"
    )

    args = parser.parse_args()

    # Get the script path (should be in same directory)
    script_path = Path(__file__).parent / "routine_detection_v3.sh"

    if not script_path.exists():
        eprint("[ERROR] Script not found: {}".format(script_path))
        sys.exit(1)

    # Build command
    cmd = [
        "bash",
        str(script_path),
        "--user={}".format(args.user),
        "RUN_NUMBER={}".format(args.run_number),
        "EXP_NUMBER={}".format(args.exp_number),
        "SAVE_NORMALIZED={}".format(args.save_normalized),
        "MAX_EVENTS={}".format(args.max_events),
        "USE_NORMALIZED={}".format(args.use_normalized),
        "NUM_PARTS={}".format(args.num_parts),
    ]

    print("[INFO] ============================================")
    print("[INFO] COYOTE XTC DETECTION LAUNCHER")
    print("[INFO] ============================================")
    print("[INFO] User: {}".format(args.user))
    print("[INFO] Run Number: {}".format(args.run_number))
    print("[INFO] Experiment: {}".format(args.exp_number))
    print("[INFO] Save Normalized: {}".format(args.save_normalized))
    print("[INFO] Max Events: {}".format(args.max_events))
    print("[INFO] Use Normalized: {}".format(args.use_normalized))
    print("[INFO] Num Parts: {}".format(args.num_parts))
    print("[INFO] ============================================")
    print()

    print("[INFO] Command: {}".format(" ".join(cmd)))
    print()

    if args.dry_run:
        print("[INFO] DRY RUN MODE - Command not executed")
        return 0

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        eprint("\n[INFO] Interrupted by user")
        return 130
    except Exception as e:
        eprint("[ERROR] Failed to execute command: {}".format(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
