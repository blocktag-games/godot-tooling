#!/usr/bin/env python3
"""W18: Waiting child. Sleeps for a known, fixed interval while
requesting negligible CPU work -- exists specifically so wall time and
CPU time can be compared SEPARATELY (per docs/benchmarks/workload-
catalog.tsv's calibration_rule), which a CPU-bound workload can't do:
a correct measurement here should show wall time near the requested
interval and CPU time near zero, and a harness bug that conflates the
two (e.g. summing wait time into a "cpu_time" column) is exactly what
this workload is built to expose.

Behavior check: the process must complete (not time out or crash) and
must print back the exact interval it was asked to wait, so a
mismatch between "requested" and "what actually happened" is visible
without needing to trust the harness's own timing code to catch it.

Usage: w18_wait.py <seconds>
"""
import sys
import time


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: w18_wait.py <seconds>", file=sys.stderr)
        return 2
    seconds = float(sys.argv[1])
    time.sleep(seconds)
    print(f"waited={seconds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
