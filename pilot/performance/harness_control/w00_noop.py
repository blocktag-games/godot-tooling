#!/usr/bin/env python3
"""W00: No-op child. One synthetic process with a specified exit code
and output -- exposes the harness's own fixed process-launch/reap
overhead (process_time, harness_cpu) independent of any real work,
per docs/benchmarks/workload-catalog.tsv. Deliberately does nothing
else: no imports beyond sys, no computation, so this workload's own
footprint is as close to the floor as CPython allows.

Behavior check (exact, not approximate): the exit code and stdout
bytes must match exactly what was requested -- this is the workload's
entire fixed_work contract, and calibration_rule explicitly forbids
lengthening it.

Usage: w00_noop.py <exit_code> <stdout_text>
"""
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: w00_noop.py <exit_code> <stdout_text>", file=sys.stderr)
        return 2
    exit_code = int(sys.argv[1])
    stdout_text = sys.argv[2]
    sys.stdout.write(stdout_text)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
