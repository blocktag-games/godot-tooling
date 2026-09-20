#!/usr/bin/env python3
"""W02: Straight-line arithmetic (scaling_control). Fixed integer
operation batches at 1x/2x/4x sizes -- a pure-CPU workload with an
ANALYTICALLY CHECKABLE result, per docs/benchmarks/workload-catalog.tsv,
so behavior can be verified exactly at any size rather than merely
"it ran and produced a number."

Computes sum(i*i for i in range(n)) via a straight-line loop (no
Python-level function-call overhead inside the loop, to keep this a
CPU/interpreter-dispatch workload rather than a call-overhead one --
that's W04's job). The closed form n(n-1)(2n-1)/6 gives an exact
expected value for any n, independent of how the loop computed it --
the behavior check does not need to re-run the loop to verify it.

calibration_rule: pilot the BASE size (n at 1x) against B0 timing, then
freeze n, 2n, 4n for every condition -- never re-pilot per condition.

Usage: w02_arithmetic.py <n>
"""
import sys


def compute(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total


def analytic_checksum(n: int) -> int:
    """Closed form for sum(i*i for i in range(n)) = sum_{i=0}^{n-1} i^2."""
    if n <= 0:
        return 0
    m = n - 1
    return m * (m + 1) * (2 * m + 1) // 6


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: w02_arithmetic.py <n>", file=sys.stderr)
        return 2
    n = int(sys.argv[1])
    result = compute(n)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
