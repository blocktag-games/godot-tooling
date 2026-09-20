#!/usr/bin/env python3
"""BP07: calibrate each workload's fixed input size against gd-tools/
GUT's B0 timing (the LIGHTER of the two candidates' runners), per
docs/benchmarks/performance-protocol.md's "Pilot 1-5 second B0 work;
identical counts thereafter" rule.

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

**Corrected 2026-09-20 (second pass): the ORIGINAL search here used
proportional scaling (new_n = old_n * target/elapsed), which is the
WRONG model.** Total elapsed time is AFFINE in n (elapsed = fixed_floor
+ k*n), not proportional through the origin -- a fixed process/GUT
startup floor of ~3.4-3.6s dominates completely at small-to-moderate n
(confirmed: n=1 and n=100,000 both land at ~3.4-3.5s; only n=10,000,000
shows a real, measurable ~1.1s increase). Proportional scaling against
an affine relationship converges falsely: if elapsed is already near
the target because of the FLOOR alone, the multiplier is ~1 and the
search "converges" after one iteration without ever actually finding a
size where the workload's own compute matters. This is exactly what
happened to the first (later-retracted-for-an-unrelated-reason)
calibration run.

Fixed by fitting an explicit two-point linear model (floor, slope) from
two real probes at deliberately different orders of magnitude, then
solving directly for the n that lands at TARGET_SECONDS, with one
confirmation probe at the solved n.

Run: python3 calibrate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS  # noqa: E402
from run_condition import run_condition  # noqa: E402

TARGET_SECONDS = 4.2  # leaves ~0.8s headroom under the protocol's 5s ceiling
TARGET_LOW, TARGET_HIGH = 1.0, 5.0


def probe(workload: str, env: dict[str, str], scratch_label: str) -> float:
    result = run_condition(GD_TOOLS, workload, "B0", extra_env=env, scratch_label=scratch_label)
    if not result.behavior_ok:
        raise RuntimeError(f"calibration probe failed behavior check: {workload} {env}\n{result.stdout}\n{result.stderr}")
    return result.process_interval_seconds


def linear_calibrate(workload: str, env_var: str, low_n: int, high_n: int) -> tuple[int, float, dict]:
    """Two-point affine fit: elapsed = floor + slope*n. Solves directly
    for the n landing at TARGET_SECONDS, then confirms with one more
    probe at that solved value."""
    t_low = probe(workload, {env_var: str(low_n)}, f"calibrate-{workload}-low")
    print(f"  probe: {env_var}={low_n} -> {t_low:.3f}s")
    t_high = probe(workload, {env_var: str(high_n)}, f"calibrate-{workload}-high")
    print(f"  probe: {env_var}={high_n} -> {t_high:.3f}s")

    slope = (t_high - t_low) / (high_n - low_n)
    floor = t_low - slope * low_n
    if slope <= 0:
        raise RuntimeError(
            f"{workload}: non-positive slope ({slope:.3e}) between n={low_n} and n={high_n} "
            f"-- the workload's size doesn't appear to affect timing at all; check the workload "
            f"actually reads {env_var} and does proportional work"
        )
    target_n = max(1, round((TARGET_SECONDS - floor) / slope))

    t_confirm = probe(workload, {env_var: str(target_n)}, f"calibrate-{workload}-confirm")
    print(f"  fit: floor={floor:.3f}s slope={slope:.3e}s/unit -> solved n={target_n}")
    print(f"  confirm: {env_var}={target_n} -> {t_confirm:.3f}s")
    if not (TARGET_LOW <= t_confirm <= TARGET_HIGH):
        raise RuntimeError(f"{workload}: confirmation probe {t_confirm:.3f}s outside [{TARGET_LOW}, {TARGET_HIGH}]s -- refit needed")

    return target_n, t_confirm, {"floor_seconds": floor, "slope_seconds_per_unit": slope, "low_n": low_n, "low_seconds": t_low, "high_n": high_n, "high_seconds": t_high}


def calibrate_w05() -> tuple[dict[str, int], float, dict]:
    """W05's dominant cost driver is total callback invocations =
    n_listeners * (n_direct + n_deferred); scale n_direct/n_deferred
    together (shared value n), holding n_listeners fixed."""
    n_listeners = 50

    def probe_n(n: int, label: str) -> float:
        env = {"PERF_W05_N_LISTENERS": str(n_listeners), "PERF_W05_N_DIRECT": str(n), "PERF_W05_N_DEFERRED": str(n)}
        return probe("w05", env, f"calibrate-w05-{label}")

    # high_n is deliberately conservative: 5,000,000 queued deferred
    # calls (call_deferred("emit_signal", ...) with no frame drain in
    # between) crashed the engine outright with "Message queue out of
    # memory" followed by a SIGSEGV -- confirmed directly, not assumed.
    # A real ceiling on how large n_deferred can practically be before
    # hitting an engine resource limit, worth recording as its own
    # finding (see calibration_result.json's w05.engine_limit_note).
    low_n, high_n = 500, 200_000
    t_low = probe_n(low_n, "low")
    print(f"  probe: n_direct=n_deferred={low_n} -> {t_low:.3f}s")
    t_high = probe_n(high_n, "high")
    print(f"  probe: n_direct=n_deferred={high_n} -> {t_high:.3f}s")

    slope = (t_high - t_low) / (high_n - low_n)
    floor = t_low - slope * low_n
    if slope <= 0:
        raise RuntimeError(f"w05: non-positive slope ({slope:.3e}) -- size doesn't appear to affect timing")
    target_n = max(1, round((TARGET_SECONDS - floor) / slope))

    t_confirm = probe_n(target_n, "confirm")
    print(f"  fit: floor={floor:.3f}s slope={slope:.3e}s/unit -> solved n={target_n}")
    print(f"  confirm: n_direct=n_deferred={target_n} -> {t_confirm:.3f}s")
    if not (TARGET_LOW <= t_confirm <= TARGET_HIGH):
        raise RuntimeError(f"w05: confirmation probe {t_confirm:.3f}s outside [{TARGET_LOW}, {TARGET_HIGH}]s -- refit needed")

    return (
        {"n_listeners": n_listeners, "n_direct": target_n, "n_deferred": target_n},
        t_confirm,
        {
            "floor_seconds": floor, "slope_seconds_per_unit": slope,
            "low_n": low_n, "low_seconds": t_low, "high_n": high_n, "high_seconds": t_high,
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
    n03, elapsed03, fit03 = linear_calibrate("w03", "PERF_W03_N", low_n=1000, high_n=20_000_000)
    results["w03"] = {"n": n03, "final_b0_seconds": elapsed03, "fit": fit03}
    print(f"  FROZEN: n={n03} ({elapsed03:.3f}s)")

    print("=== W05 (signals and deferred dispatch) ===")
    w05_params, elapsed05, fit05 = calibrate_w05()
    results["w05"] = {**w05_params, "final_b0_seconds": elapsed05, "fit": fit05}
    print(f"  FROZEN: {w05_params} ({elapsed05:.3f}s)")

    print("=== W11 (representative scene application) ===")
    n11, elapsed11, fit11 = linear_calibrate("w11", "PERF_W11_N_STEPS", low_n=100, high_n=2_000_000)
    results["w11"] = {"n_steps": n11, "seed": 12345, "final_b0_seconds": elapsed11, "fit": fit11}
    print(f"  FROZEN: n_steps={n11}, seed=12345 ({elapsed11:.3f}s)")

    out_path = Path(__file__).parent / "calibration_result.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
