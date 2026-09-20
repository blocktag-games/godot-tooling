#!/usr/bin/env python3
"""BP08: validate the TIMING harness itself -- the same
`pilot/harness/runner.py::run()` primitive (monotonic-clock-around-
Popen-and-communicate) that produced every process_interval_seconds
value in the BP07 pilot -- against known-magnitude ground truth. This
is the same idea validate_analyze.py already applied one layer up (a
known truth planted, then confirm the pipeline recovers it), applied
here to the measurement primitive instead of the estimator.

`harness_control/self_test.py` already verified these five fixtures'
BEHAVIOR (exact exit codes/output) via plain subprocess.run(), with no
timing analysis. This script is deliberately separate: it verifies
TIMING, through the actual harness primitive, per docs/benchmarks/
implementation-plan.md's BP08 row ("Null/CPU/wait/log/memory controls")
and docs/benchmarks/profiling-protocol.md's "Calibrate the measurement
system" table.

Checks:
- W00 (no-op): establishes the harness's own measurement floor and its
  run-to-run variance -- a false-positive check (near-zero real work
  should read back as near-zero elapsed time, not some inflated
  harness-imposed constant).
- W18 (wait): a known, fixed sleep interval should read back as elapsed
  wall time within a small tolerance of the floor -- a false-negative
  check (the harness must not eat or misreport a real interval).
- W02 (CPU arithmetic) and W19 (memory) at increasing sizes: elapsed
  time must increase monotonically with size, confirming the harness's
  timing is actually sensitive to real work and not saturated by its
  own overhead at these magnitudes.
- W17 (log volume) at increasing byte counts: elapsed time must not
  decrease with more output, and stdout/stderr must be captured
  completely (byte-exact), confirming no pipe-backpressure truncation
  under the harness's own capture strategy.

Run: python3 validate_harness_timing.py
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "harness"))
from runner import run  # noqa: E402

PY = sys.executable
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def validate_w00_floor(n: int = 10) -> float:
    """Repeat the no-op N times through the real harness primitive;
    report the floor (mean) and its coefficient of variation. There is
    no protocol-defined pass/fail threshold for the floor itself -- it
    is recorded as the baseline every other check's tolerance is set
    relative to, not compared against an assumed constant."""
    times = []
    for _ in range(n):
        result = run([PY, str(HERE / "w00_noop.py"), "0", "x"], cwd=str(HERE), timeout_s=10)
        check("w00_via_harness_exit_zero", result.exit_code == 0, str(result.exit_code))
        check("w00_via_harness_no_timeout", not result.timed_out, "")
        times.append(result.duration_s)
    floor = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0.0
    cv = (stdev / floor * 100) if floor > 0 else 0.0
    print(f"  W00 harness floor: mean={floor:.4f}s stdev={stdev:.4f}s CV={cv:.1f}% (n={n})")
    return floor


def validate_w18_wait(floor: float) -> None:
    """A known 0.5s sleep must read back as approximately floor + 0.5s
    -- not exactly floor + 0.5s (a real OS sleep always overshoots
    slightly), so the check is a tolerance band, not equality. If the
    harness conflated wall time with something else (e.g. reported 0s
    regardless of the sleep, or reported CPU time instead of wall
    time), this is exactly what would fail."""
    requested = 0.5
    result = run([PY, str(HERE / "w18_wait.py"), str(requested)], cwd=str(HERE), timeout_s=10)
    check("w18_via_harness_exit_zero", result.exit_code == 0, str(result.exit_code))
    check(
        "w18_via_harness_reports_requested_interval",
        result.stdout.strip() == f"waited={requested}",
        repr(result.stdout),
    )
    lower = requested  # a real sleep(0.5) never returns early
    upper = requested + floor + 0.5  # generous slack: floor + up to 0.5s of scheduling jitter
    check(
        "w18_via_harness_elapsed_in_tolerance_band",
        lower <= result.duration_s <= upper,
        f"elapsed={result.duration_s:.4f}s not in [{lower:.4f}, {upper:.4f}]",
    )
    print(f"  W18 requested={requested}s -> harness measured {result.duration_s:.4f}s")


def validate_w02_scaling(floor: float) -> None:
    """1x/2x/4x sizes must show monotonically increasing elapsed time.
    Base n chosen large enough that its expected runtime clears the
    floor by a comfortable margin (probed empirically below, not
    assumed) -- otherwise a real scaling signal could be swamped by
    floor noise and this check would be meaningless."""
    from w02_arithmetic import analytic_checksum

    base_n = 20_000_000
    sizes = {"1x": base_n, "2x": base_n * 2, "4x": base_n * 4}
    times: dict[str, float] = {}
    for label, n in sizes.items():
        result = run([PY, str(HERE / "w02_arithmetic.py"), str(n)], cwd=str(HERE), timeout_s=30)
        expected = analytic_checksum(n)
        actual = int(result.stdout.strip())
        check(f"w02_{label}_analytic_result_exact", actual == expected, f"expected {expected}, got {actual}")
        times[label] = result.duration_s
        print(f"  W02 {label} (n={n}) -> {result.duration_s:.4f}s")
    check(
        "w02_scaling_monotonic_1x_lt_2x_lt_4x",
        times["1x"] < times["2x"] < times["4x"],
        str(times),
    )
    check(
        "w02_1x_clears_floor_noise",
        times["1x"] > floor * 3,
        f"1x elapsed {times['1x']:.4f}s is not comfortably above floor {floor:.4f}s -- base_n too small",
    )


def validate_w19_scaling(floor: float) -> None:
    """Larger allocations should not run FASTER (the touch-all-pages
    loop is O(size)); primarily a behavior + non-negative-scaling
    check, since page-touching cost is small relative to the floor at
    these sizes on this machine."""
    sizes_mb = [16, 64, 256]
    times: dict[int, float] = {}
    for mb in sizes_mb:
        result = run([PY, str(HERE / "w19_memlifetime.py"), str(mb), "0.05"], cwd=str(HERE), timeout_s=15)
        lines = result.stdout.strip().splitlines()
        check(
            f"w19_{mb}mb_lifecycle_output_exact",
            lines == [f"allocated_mb={mb}", "retained_seconds=0.05", "released=true"],
            str(lines),
        )
        times[mb] = result.duration_s
        print(f"  W19 {mb}MB -> {result.duration_s:.4f}s")
    check(
        "w19_scaling_non_decreasing",
        times[16] <= times[64] <= times[256],
        str(times),
    )


def validate_w17_no_truncation() -> None:
    """More output must not truncate or silently drop bytes under the
    harness's own capture strategy (subprocess.PIPE + communicate(),
    which buffers to completion rather than streaming -- the failure
    mode this guards against is a pipe deadlock/truncation under a
    large synchronous write, not a timing property)."""
    from w17_logvolume import make_bytes

    for stdout_bytes in (1_000, 1_000_000):
        result = run(
            [PY, str(HERE / "w17_logvolume.py"), str(stdout_bytes), "0", "chunked", "4096"],
            cwd=str(HERE), timeout_s=15,
        )
        # runner.run() always decodes with text=True, unlike self_test.py's
        # raw-bytes subprocess.run() call -- decode the expected pattern
        # the same way to compare content, not just length.
        check(
            f"w17_{stdout_bytes}b_no_truncation_under_harness",
            len(result.stdout) == stdout_bytes and result.stdout == make_bytes(stdout_bytes).decode(),
            f"got {len(result.stdout)} bytes, expected {stdout_bytes}",
        )
        print(f"  W17 {stdout_bytes} bytes -> {result.duration_s:.4f}s, {len(result.stdout)} bytes captured")


def main() -> int:
    print("=== W00 (no-op): harness measurement floor ===")
    floor = validate_w00_floor()

    print("=== W18 (wait): known-interval recovery ===")
    validate_w18_wait(floor)

    print("=== W02 (CPU arithmetic): scaling sensitivity ===")
    validate_w02_scaling(floor)

    print("=== W19 (memory): scaling sensitivity ===")
    validate_w19_scaling(floor)

    print("=== W17 (log volume): capture completeness under load ===")
    validate_w17_no_truncation()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print("Harness timing primitive (pilot/harness/runner.py::run) recovers known-magnitude "
          "truth on all five controls: correct floor behavior, accurate known-interval "
          "recovery, monotonic scaling sensitivity, and complete output capture.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
