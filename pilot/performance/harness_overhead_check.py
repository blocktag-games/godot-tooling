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
reproducible number in the observer matrix rather than an unverified
claim.

Run: python3 harness_overhead_check.py
"""
from __future__ import annotations

import statistics
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS, REPO_ROOT, GODOT_BIN, setup_scratch_project
from run_condition import run_condition

SCRATCH_ROOT = Path("/tmp/perf-run-h-check")
REPEATS = 5


def main() -> int:
    import os
    scratch_dir = SCRATCH_ROOT / "gd-tools-w01"
    setup_scratch_project(GD_TOOLS, "B0", scratch_dir)
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    subprocess.run([str(GODOT_BIN), "--headless", "--path", str(scratch_dir), "--import"], cwd=str(scratch_dir), env=env, timeout=60)

    gd_tools_bin = str(REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools")
    cmd = [gd_tools_bin, "test", "--test", "test_w01"]

    h0_times = []
    print(f"=== H=0 (minimal_launcher.py), n={REPEATS} ===")
    for i in range(REPEATS):
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "minimal_launcher.py"), str(scratch_dir)] + cmd,
            capture_output=True, text=True, env=env, timeout=60,
        )
        t = float(proc.stdout.strip())
        h0_times.append(t)
        print(f"  rep {i}: {t:.4f}s")

    h1_times = []
    print(f"=== H=1 (run_condition.py full orchestration), n={REPEATS} ===")
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
    print()
    print(f"H=0 mean={h0_mean:.4f}s stdev={h0_stdev:.4f}s")
    print(f"H=1 mean={h1_mean:.4f}s stdev={h1_stdev:.4f}s")
    print(f"H=1/H=0 ratio: {ratio:.4f} ({(ratio - 1) * 100:+.2f}%)")
    pooled_stdev = (h0_stdev + h1_stdev) / 2
    within_noise = abs(h1_mean - h0_mean) < 2 * pooled_stdev
    print(
        f"H1-H0 difference ({abs(h1_mean - h0_mean):.4f}s) is "
        f"{'within' if within_noise else 'OUTSIDE'} 2x pooled per-condition stdev ({2 * pooled_stdev:.4f}s)"
    )
    return 0 if within_noise else 1


if __name__ == "__main__":
    raise SystemExit(main())
