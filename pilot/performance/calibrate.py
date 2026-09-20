#!/usr/bin/env python3
"""BP07: calibrate each workload's fixed input size against gd-tools/
GUT's B0 timing (the LIGHTER of the two candidates' runners), per
docs/benchmarks/performance-protocol.md's "Pilot 1-5 second B0 work;
identical counts thereafter" rule and docs/benchmarks/workload-
catalog.tsv's calibration_rule for W03/W05/W11.

Calibrating against one reference candidate and freezing that size for
BOTH candidates is deliberate, not an oversight: the fixed-work unit
must be IDENTICAL across candidates for their C/B0 ratios to be
comparable to each other at all. Nano Coverage's own B0 will simply
take longer under the same n -- that is the real runner-cost
difference the per-candidate-baseline design already exists to
capture, not something to calibrate away by giving each candidate its
own n.

W01 has no calibratable size at all (its own catalog rule: "No
artificial useful-work expansion") -- not probed here.

**Corrected 2026-09-20 (THIRD pass): the SECOND pass calibrated the
wrong metric.** It correctly fit an affine model (elapsed = floor +
k*n) instead of the first pass's wrong proportional-scaling search, but
it fit and targeted TOTAL PROCESS TIME (process_interval_seconds),
which includes a ~3.4-3.6s fixed process/GUT-or-GdUnit4 startup floor
that has nothing to do with the workload's own size. The catalog's
"1-5 seconds of B0 work" means the WORKLOAD's useful work, not the
whole process -- at the second pass's frozen sizes, actual measured
work time (via the new work_time_seconds field, an in-process
Time.get_ticks_usec() span around the fixed-work call only) turned out
to be only 0.26-0.84s, under the catalog's 1s minimum, meaning most of
every C/B0 ratio in the BP07 pilot was startup-floor dilution rather
than real per-work overhead.

Fixed: this pass fits and targets work_time_seconds directly (still via
a two-point affine model -- work time is approximately affine in n for
these workloads, dominated by per-iteration cost rather than a
per-call floor, but not assumed proportional through the origin
without checking). A confirmation probe validates the fit, same as
before. NEW this pass: after finding the target n, one COVERAGE-ACTIVE
(condition C) probe is run before freezing anything, to verify the
resulting run's real process time (floor + inflated work time under
instrumentation) stays safely under run_condition.py's 120s timeout --
a pure B0 calibration cannot see this, since coverage multiplies work
time by 9-15x in early spot checks, and freezing a size whose C
condition later hits the timeout mid-pilot would silently produce a
truncated, useless row instead of real data.

Run: python3 calibrate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS  # noqa: E402
from run_condition import run_condition  # noqa: E402

TARGET_WORK_SECONDS = 2.0  # within the protocol's 1-5s band, leaving headroom for variance
TARGET_LOW, TARGET_HIGH = 1.0, 4.5
C_PROBE_TIMEOUT_BUDGET_S = 90.0  # comfortably under run_condition.py's 120s hard timeout


def probe(workload: str, env: dict[str, str], scratch_label: str, condition: str = "B0") -> tuple[float, float]:
    """Returns (work_time_seconds, process_interval_seconds)."""
    result = run_condition(GD_TOOLS, workload, condition, extra_env=env, scratch_label=scratch_label)
    if not result.behavior_ok:
        raise RuntimeError(f"calibration probe failed behavior check: {workload} {condition} {env}\n{result.stdout}\n{result.stderr}")
    if result.work_time_seconds is None:
        raise RuntimeError(f"calibration probe produced no work_time_seconds: {workload} {condition} {env}")
    return result.work_time_seconds, result.process_interval_seconds


def check_c_condition_budget(workload: str, env: dict[str, str], scratch_label: str) -> float:
    """Confirms the frozen size's COVERAGE-ACTIVE run finishes with
    comfortable margin under the timeout, not just its B0 run."""
    c_work_s, c_process_s = probe(workload, env, scratch_label, condition="C")
    print(f"  C-condition budget check: work_time={c_work_s:.3f}s process_time={c_process_s:.3f}s")
    if c_process_s > C_PROBE_TIMEOUT_BUDGET_S:
        raise RuntimeError(
            f"{workload}: coverage-active process time {c_process_s:.1f}s exceeds the "
            f"{C_PROBE_TIMEOUT_BUDGET_S}s budget (hard timeout is 120s) -- reduce TARGET_WORK_SECONDS"
        )
    return c_process_s


def linear_calibrate(workload: str, env_var: str, low_n: int, high_n: int) -> tuple[int, float, dict]:
    """Two-point affine fit of WORK TIME (not process time) against n:
    work_time = floor + slope*n. Solves directly for the n landing at
    TARGET_WORK_SECONDS, then confirms with one more B0 probe plus one
    C-condition timeout-budget probe at that solved value."""
    work_low, proc_low = probe(workload, {env_var: str(low_n)}, f"calibrate-{workload}-low")
    print(f"  probe: {env_var}={low_n} -> work_time={work_low:.4f}s process_time={proc_low:.3f}s")
    work_high, proc_high = probe(workload, {env_var: str(high_n)}, f"calibrate-{workload}-high")
    print(f"  probe: {env_var}={high_n} -> work_time={work_high:.4f}s process_time={proc_high:.3f}s")

    slope = (work_high - work_low) / (high_n - low_n)
    floor = work_low - slope * low_n
    if slope <= 0:
        raise RuntimeError(
            f"{workload}: non-positive work_time slope ({slope:.3e}) between n={low_n} and n={high_n} "
            f"-- the workload's size doesn't appear to affect measured WORK TIME at all; check the "
            f"workload actually reads {env_var} and does proportional work, and that work_time_seconds "
            f"is being captured (not silently None)"
        )
    target_n = max(1, round((TARGET_WORK_SECONDS - floor) / slope))

    work_confirm, proc_confirm = probe(workload, {env_var: str(target_n)}, f"calibrate-{workload}-confirm")
    print(f"  fit: floor={floor:.4f}s slope={slope:.3e}s/unit -> solved n={target_n}")
    print(f"  confirm: {env_var}={target_n} -> work_time={work_confirm:.4f}s process_time={proc_confirm:.3f}s")
    if not (TARGET_LOW <= work_confirm <= TARGET_HIGH):
        raise RuntimeError(f"{workload}: confirmation work_time {work_confirm:.3f}s outside [{TARGET_LOW}, {TARGET_HIGH}]s -- refit needed")

    c_process_s = check_c_condition_budget(workload, {env_var: str(target_n)}, f"calibrate-{workload}-cprobe")

    return target_n, work_confirm, {
        "floor_seconds": floor, "slope_seconds_per_unit": slope,
        "low_n": low_n, "low_work_seconds": work_low, "low_process_seconds": proc_low,
        "high_n": high_n, "high_work_seconds": work_high, "high_process_seconds": proc_high,
        "confirm_process_seconds": proc_confirm, "c_condition_process_seconds": c_process_s,
    }


def calibrate_w05() -> tuple[dict[str, int], float, dict]:
    """W05's dominant cost driver is total callback invocations =
    n_listeners * (n_direct + n_deferred); scale n_direct/n_deferred
    together (shared value n), holding n_listeners fixed."""
    n_listeners = 50

    def probe_n(n: int, label: str, condition: str = "B0") -> tuple[float, float]:
        env = {"PERF_W05_N_LISTENERS": str(n_listeners), "PERF_W05_N_DIRECT": str(n), "PERF_W05_N_DEFERRED": str(n)}
        return probe("w05", env, f"calibrate-w05-{label}", condition=condition)

    # high_n is deliberately conservative: 5,000,000 queued deferred
    # calls (call_deferred("emit_signal", ...) with no frame drain in
    # between) crashed the engine outright with "Message queue out of
    # memory" followed by a SIGSEGV -- confirmed directly, not assumed.
    # A real ceiling on how large n_deferred can practically be before
    # hitting an engine resource limit, worth recording as its own
    # finding (see calibration_result.json's w05.engine_limit_note).
    low_n, high_n = 500, 200_000
    work_low, proc_low = probe_n(low_n, "low")
    print(f"  probe: n_direct=n_deferred={low_n} -> work_time={work_low:.4f}s process_time={proc_low:.3f}s")
    work_high, proc_high = probe_n(high_n, "high")
    print(f"  probe: n_direct=n_deferred={high_n} -> work_time={work_high:.4f}s process_time={proc_high:.3f}s")

    slope = (work_high - work_low) / (high_n - low_n)
    floor = work_low - slope * low_n
    if slope <= 0:
        raise RuntimeError(f"w05: non-positive work_time slope ({slope:.3e}) -- size doesn't appear to affect measured work time")
    target_n = max(1, round((TARGET_WORK_SECONDS - floor) / slope))

    work_confirm, proc_confirm = probe_n(target_n, "confirm")
    print(f"  fit: floor={floor:.4f}s slope={slope:.3e}s/unit -> solved n={target_n}")
    print(f"  confirm: n_direct=n_deferred={target_n} -> work_time={work_confirm:.4f}s process_time={proc_confirm:.3f}s")
    if not (TARGET_LOW <= work_confirm <= TARGET_HIGH):
        raise RuntimeError(f"w05: confirmation work_time {work_confirm:.3f}s outside [{TARGET_LOW}, {TARGET_HIGH}]s -- refit needed")

    c_env = {"PERF_W05_N_LISTENERS": str(n_listeners), "PERF_W05_N_DIRECT": str(target_n), "PERF_W05_N_DEFERRED": str(target_n)}
    c_process_s = check_c_condition_budget("w05", c_env, "calibrate-w05-cprobe")

    return (
        {"n_listeners": n_listeners, "n_direct": target_n, "n_deferred": target_n},
        work_confirm,
        {
            "floor_seconds": floor, "slope_seconds_per_unit": slope,
            "low_n": low_n, "low_work_seconds": work_low, "low_process_seconds": proc_low,
            "high_n": high_n, "high_work_seconds": work_high, "high_process_seconds": proc_high,
            "confirm_process_seconds": proc_confirm, "c_condition_process_seconds": c_process_s,
            "engine_limit_note": (
                "5,000,000 queued deferred calls (call_deferred('emit_signal', ...) "
                "with no frame drain in between) crashed the engine with 'Message "
                "queue out of memory' followed by a SIGSEGV -- confirmed directly "
                "2026-09-20. A real ceiling on n_deferred well below what the "
                "calibration search would otherwise try, not a measurement artifact."
            ),
        },
    )


def main() -> int:
    results: dict[str, dict] = {}

    print("=== W03 (branch-heavy logic) ===")
    n03, work03, fit03 = linear_calibrate("w03", "PERF_W03_N", low_n=1000, high_n=20_000_000)
    results["w03"] = {"n": n03, "final_b0_work_seconds": work03, "fit": fit03}
    print(f"  FROZEN: n={n03} (work_time={work03:.4f}s)")

    print("=== W05 (signals and deferred dispatch) ===")
    w05_params, work05, fit05 = calibrate_w05()
    results["w05"] = {**w05_params, "final_b0_work_seconds": work05, "fit": fit05}
    print(f"  FROZEN: {w05_params} (work_time={work05:.4f}s)")

    print("=== W11 (representative scene application) ===")
    n11, work11, fit11 = linear_calibrate("w11", "PERF_W11_N_STEPS", low_n=100, high_n=2_000_000)
    results["w11"] = {"n_steps": n11, "seed": 12345, "final_b0_work_seconds": work11, "fit": fit11}
    print(f"  FROZEN: n_steps={n11}, seed=12345 (work_time={work11:.4f}s)")

    out_path = Path(__file__).parent / "calibration_result.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
