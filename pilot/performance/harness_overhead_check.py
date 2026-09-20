#!/usr/bin/env python3
"""BP08: spot-check the H (harness) factor of profiling-protocol.md's
factorial observer experiment -- H=0 (minimal_launcher.py) vs H=1
(run_condition.py's full orchestration) -- for the identical already-
built scratch project and command.

Scope note (deliberate, matching this project's established pattern of
recording reduced-scope decisions rather than treating them as gaps):
this is a SPOT CHECK, not the full "two sessions of five eight-
condition blocks" pilot profiling-protocol.md describes for the
complete H x C x P factorial. That full design multiplies out to
workload x collector x profiler combinations x sessions x blocks x 8
launches (implementation-plan.md's own worked example: 240 launches
for a 3-workload/1-collector/1-profiler 2x5 pilot) -- and P (profiler)
is not available this session (perf unavailable; Godot's built-in
profiler and a Tracy build not validated), collapsing the design to
H x C x 4 conditions before any pilot launch count is chosen.

The reason a lighter check suffices here: run_condition.py's own
structure already makes an H effect implausible by construction --
harness_profile.py's cProfile capture showed ALL of run_condition()'s
own Python-side bookkeeping (scratch setup, dataclass construction,
behavior/artifact checks) happens OUTSIDE the timed window that
runner.run() measures; the timed interval itself is the identical
runner.run() call in both H=0 and H=1. A full factorial pilot would be
measuring the same primitive twice under two thin wrappers. This spot
check exists to confirm that structural argument empirically rather
than asserting it from code-reading alone -- and to leave a documented,
reproducible raw record rather than a single unverified point estimate.

**Corrected 2026-09-20, a Fable review of this BP08 phase:**
- The first version rebuilt the scratch project/import cache once for
  H=0 and reused it across all 5 reps, while H=1 (via run_condition())
  rebuilds and re-imports before EVERY rep -- an unmatched workspace
  state between arms (profiling-protocol.md:78 asks for "equivalent
  workspaces"). Fixed: both arms now rebuild/re-import per rep.
- The first version reported a single point estimate ("-0.45%") with no
  saved raw reps, and that number was NOT reproducible on a rerun (a
  second, independent run got +0.93% -- consistent with "no detectable
  effect", but the point estimate itself is noise, not a stable
  measurement). Fixed: this script now writes its raw per-rep times to
  harness_overhead_check_result.json and reports the result as a
  bounded claim ("not distinguishable from zero at the achieved
  resolution"), not a specific percentage to two decimal places.

Run: python3 harness_overhead_check.py
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS, REPO_ROOT, GODOT_BIN, setup_scratch_project
from run_condition import run_condition

SCRATCH_ROOT = Path("/tmp/perf-run-h-check")
REPEATS = 5
OUT_JSON = Path(__file__).parent / "harness_overhead_check_result.json"


def rebuild_and_import(scratch_dir: Path, env: dict[str, str]) -> None:
    setup_scratch_project(GD_TOOLS, "B0", scratch_dir)
    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(scratch_dir), "--import"],
        cwd=str(scratch_dir), env=env, timeout=60, capture_output=True,
    )


def main() -> int:
    import os
    scratch_dir = SCRATCH_ROOT / "gd-tools-w01"
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)

    gd_tools_bin = str(REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools")
    cmd = [gd_tools_bin, "test", "--test", "test_w01"]

    h0_times = []
    print(f"=== H=0 (minimal_launcher.py), n={REPEATS}, rebuild+reimport per rep ===")
    for i in range(REPEATS):
        rebuild_and_import(scratch_dir, env)
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "minimal_launcher.py"), str(scratch_dir)] + cmd,
            capture_output=True, text=True, env=env, timeout=60,
        )
        t = float(proc.stdout.strip())
        h0_times.append(t)
        print(f"  rep {i}: {t:.4f}s")

    h1_times = []
    print(f"=== H=1 (run_condition.py full orchestration), n={REPEATS}, rebuild+reimport per rep ===")
    for i in range(REPEATS):
        result = run_condition(GD_TOOLS, "w01", "B0", scratch_label="h-check-gd-tools-w01")
        if not result.behavior_ok:
            print(f"FAIL: H=1 rep {i} did not pass behavior check", file=sys.stderr)
            return 1
        h1_times.append(result.process_interval_seconds)
        print(f"  rep {i}: {result.process_interval_seconds:.4f}s")

    h0_mean, h1_mean = statistics.mean(h0_times), statistics.mean(h1_times)
    h0_stdev = statistics.stdev(h0_times)
    h1_stdev = statistics.stdev(h1_times)
    ratio = h1_mean / h0_mean
    pooled_stdev = (h0_stdev + h1_stdev) / 2
    within_noise = abs(h1_mean - h0_mean) < 2 * pooled_stdev
    resolution_pct = 2 * pooled_stdev / h0_mean * 100

    OUT_JSON.write_text(json.dumps({
        "h0_times": h0_times, "h1_times": h1_times,
        "h0_mean": h0_mean, "h1_mean": h1_mean,
        "h0_stdev": h0_stdev, "h1_stdev": h1_stdev,
        "ratio": ratio, "within_noise": within_noise,
        "achieved_resolution_pct": resolution_pct,
    }, indent=2))

    print()
    print(f"H=0 mean={h0_mean:.4f}s stdev={h0_stdev:.4f}s")
    print(f"H=1 mean={h1_mean:.4f}s stdev={h1_stdev:.4f}s")
    print(f"H=1/H=0 ratio: {ratio:.4f} ({(ratio - 1) * 100:+.2f}%)")
    print(
        f"H1-H0 difference ({abs(h1_mean - h0_mean):.4f}s) is "
        f"{'within' if within_noise else 'OUTSIDE'} 2x pooled per-condition stdev ({2 * pooled_stdev:.4f}s)"
    )
    print(
        f"With n={REPEATS} reps per arm, this spot check can only resolve an H effect larger "
        f"than ~{resolution_pct:.1f}% at this workload's duration -- report the finding as "
        f"'not distinguishable from zero at this resolution', NOT as a specific point-estimate "
        f"percentage (a rerun's point estimate is not stable; see module docstring). "
        f"Raw reps saved to {OUT_JSON.name}."
    )
    return 0 if within_noise else 1


if __name__ == "__main__":
    raise SystemExit(main())
