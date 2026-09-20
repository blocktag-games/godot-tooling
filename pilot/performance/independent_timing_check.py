#!/usr/bin/env python3
"""BP08: independent timing cross-check, per docs/benchmarks/
implementation-plan.md's BP08 row and profiling-protocol.md's
"Calibrate the measurement system" section ("Use an independent
minimal process launcher... to cross-check complete-command elapsed
measurements... Investigate disagreement instead of averaging the
instruments.").

This deliberately does NOT re-read runner.py's code again -- the
second Fable review of BP07 already did that. It wraps the SAME
commands with a genuinely separate measurement mechanism (`/usr/bin/
time -v`, a real external process, not a re-derivation of the same
Python call) and compares its "Elapsed (wall clock) time" against
`pilot/harness/runner.py::run()`'s own process_interval_seconds for
the identical command.

What this checks:
1. Do the two independent mechanisms agree on elapsed wall time for
   the same command, within measurement noise?

**Corrected 2026-09-20, a Fable review of this BP08 phase: what this
does NOT establish.** An earlier version of this docstring claimed
that agreement between the two mechanisms was "evidence neither loses
track of a grandchild the direct child spawns and detaches from (the
F067 failure shape)". That inference is invalid and has been retracted:
both `/usr/bin/time -v` and `runner.run()`'s `communicate()` stop their
clock at the SAME boundary -- their own direct child's exit (wait4)
plus that child's stdio pipes reaching EOF. A grandchild that
double-forks and detaches from the child's stdio (the exact shape
`os.killpg()`/F067 was fixed to handle on the TIMEOUT path, not the
normal-exit path this script probes) would be invisible to BOTH
mechanisms identically -- agreement in that case would be two
instruments sharing one blind spot, not confirmation of anything. The
review demonstrated this concretely with a synthetic child that spawns
a stdio-detached grandchild sleeping 1.0s: both mechanisms under-report
by ~98% and AGREE; a stdio-inheriting grandchild makes them disagree
(the harness reports correctly, `/usr/bin/time` still doesn't).

The actual evidence this script has for "the candidate's real process
tree was fully waited-for," printed below as `child_cpu_mean`, is
`/usr/bin/time -v`'s own User+System time, which sums the rusage of
every REAPED descendant (not just the direct child) -- for gd-tools
that is ~3.0s of ~3.4s wall, for Nano Coverage ~1.4s of ~1.8s wall,
both a large majority of wall time. That is real (if partial) evidence
the tree was reaped rather than detached; it does not rule out a
detached grandchild contributing zero to the wall-time comparison
above. This script's real, valid contribution is #1: a clock-arithmetic
sanity check that two differently-implemented timers agree on elapsed
wall time for the same command.

Run: python3 independent_timing_check.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "harness_control"))
sys.path.insert(0, str(HERE.parent / "harness"))
from runner import run as harness_run  # noqa: E402

sys.path.insert(0, str(HERE))
from candidates import GD_TOOLS, NANO_COVERAGE, REPO_ROOT, GODOT_BIN, setup_scratch_project  # noqa: E402

TIME_BIN = "/usr/bin/time"
SCRATCH_ROOT = Path("/tmp/perf-run-independent-check")

ELAPSED_RE = re.compile(r"Elapsed \(wall clock\) time.*?: (?:(\d+):)?(\d+):(\d+\.\d+)")
USER_RE = re.compile(r"User time \(seconds\): (\d+\.\d+)")
SYS_RE = re.compile(r"System time \(seconds\): (\d+\.\d+)")

RESULTS: list[dict] = []


def parse_elapsed(time_stderr: str) -> float:
    m = ELAPSED_RE.search(time_stderr)
    if not m:
        raise RuntimeError(f"could not parse /usr/bin/time -v output:\n{time_stderr}")
    hours, minutes, seconds = m.groups()
    total = int(minutes) * 60 + float(seconds)
    if hours:
        total += int(hours) * 3600
    return total


def parse_cpu(time_stderr: str) -> tuple[float, float]:
    user_m, sys_m = USER_RE.search(time_stderr), SYS_RE.search(time_stderr)
    return float(user_m.group(1)) if user_m else 0.0, float(sys_m.group(1)) if sys_m else 0.0


def cross_check(label: str, cmd: list[str], cwd: str, timeout_s: float, env: dict[str, str] | None = None, repeats: int = 1) -> None:
    """Two separate process launchers can never time the literal same
    execution -- each repetition here is a fresh, independent process,
    so single-shot comparison conflates "mechanism disagreement" with
    ordinary run-to-run process variance. Repeats > 1 compares MEANS,
    which is what an apples-to-apples cross-check actually requires."""
    harness_times = []
    external_times = []
    child_cpu_times = []
    for _ in range(repeats):
        harness_result = harness_run(cmd, cwd=cwd, timeout_s=timeout_s, env=env)
        harness_times.append(harness_result.duration_s)

        time_proc = subprocess.run(
            [TIME_BIN, "-v"] + cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout_s + 10, env=env,
        )
        external_times.append(parse_elapsed(time_proc.stderr))
        user_s, sys_s = parse_cpu(time_proc.stderr)
        child_cpu_times.append(user_s + sys_s)

    harness_mean = sum(harness_times) / repeats
    external_mean = sum(external_times) / repeats
    delta = harness_mean - external_mean
    delta_pct = (delta / external_mean * 100) if external_mean > 0 else float("nan")
    RESULTS.append({
        "label": label,
        "harness_s": harness_mean,
        "external_s": external_mean,
        "delta_s": delta,
        "delta_pct": delta_pct,
        "child_cpu_s": sum(child_cpu_times) / repeats,
    })
    print(
        f"{label:55s} harness_mean={harness_mean:.4f}s (n={repeats})  "
        f"external_mean(/usr/bin/time)={external_mean:.4f}s  "
        f"delta={delta:+.4f}s ({delta_pct:+.1f}%)  child_cpu_mean={sum(child_cpu_times)/repeats:.4f}s"
    )


def main() -> int:
    if not shutil.which(TIME_BIN.split("/")[-1]) and not Path(TIME_BIN).exists():
        print(f"SKIP: {TIME_BIN} not available on this machine -- cannot cross-check.", file=sys.stderr)
        return 1

    print("=== Harness-control fixtures (single process, no children) ===")
    cross_check("w00_noop", [sys.executable, str(HERE / "harness_control/w00_noop.py"), "0", "x"], str(HERE), 10, repeats=10)
    cross_check("w18_wait_0.5s", [sys.executable, str(HERE / "harness_control/w18_wait.py"), "0.5"], str(HERE), 10, repeats=5)

    print()
    print("=== Real candidate runs (process TREES -- the F067-relevant case) ===")
    import os
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)

    gd_scratch = SCRATCH_ROOT / "gd-tools-w01"
    setup_scratch_project(GD_TOOLS, "B0", gd_scratch)
    harness_run([str(GODOT_BIN), "--headless", "--path", str(gd_scratch), "--import"], cwd=str(gd_scratch), timeout_s=60, env=env)
    gd_tools_bin = str(REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools")
    cross_check(
        "gd-tools_w01_B0 (Python CLI -> godot --import -> GUT)",
        [gd_tools_bin, "test", "--test", "test_w01"], str(gd_scratch), 60, env=env, repeats=5,
    )

    nano_scratch = SCRATCH_ROOT / "nano-coverage-w01"
    setup_scratch_project(NANO_COVERAGE, "B0", nano_scratch)
    harness_run([str(GODOT_BIN), "--headless", "--path", str(nano_scratch), "--import"], cwd=str(nano_scratch), timeout_s=60, env=env)
    cross_check(
        "nano-coverage_w01_B0 (bash -> godot --version -> GdUnitCmdTool -> godot)",
        ["bash", "addons/gdUnit4/runtest.sh", "-a", "tests_gdunit/test_w01.gd"], str(nano_scratch), 60, env=env, repeats=5,
    )

    print()
    print("=== Summary ===")
    # /usr/bin/time -v reports elapsed at centisecond resolution, so a
    # near-floor command (e.g. w00's ~10ms) can show a large PERCENTAGE
    # delta from quantization noise alone despite an absolute delta of a
    # fraction of a millisecond -- flag only a disagreement that is both
    # >5% AND >20ms absolute, matched to that resolution floor.
    flagged = [r for r in RESULTS if abs(r["delta_pct"]) > 5.0 and abs(r["delta_s"]) > 0.02]
    # /usr/bin/time -v's centisecond resolution means a near-floor
    # command (w00, ~10ms) can report exactly 0.00s, making delta_pct a
    # NaN (division by ~0) -- that row carries no signal either way and
    # is reported separately rather than silently folded into "all N
    # cross-checks" as if it had been meaningfully compared.
    comparable = [r for r in RESULTS if r["delta_pct"] == r["delta_pct"]]  # drop NaN
    nan_rows = [r["label"] for r in RESULTS if r["delta_pct"] != r["delta_pct"]]
    if nan_rows:
        print(f"Excluded from comparison (external timer's resolution too coarse to compare): {nan_rows}")
    max_abs_pct = max((abs(r["delta_pct"]) for r in comparable), default=0.0)
    print(f"Largest |delta| across {len(comparable)} comparable cross-checks (of {len(RESULTS)} total): {max_abs_pct:.1f}%")
    for r in RESULTS:
        if r["harness_s"] > 0:
            print(f"  {r['label']}: child_cpu/wall = {r['child_cpu_s'] / r['harness_s'] * 100:.0f}% (reaped-descendant rusage share of wall time)")
    if flagged:
        for r in flagged:
            print(f"  DISAGREEMENT: {r['label']}: {r['delta_s']:+.4f}s ({r['delta_pct']:+.1f}%)")
        print(
            "INVESTIGATE: two independent measurement mechanisms disagree by more than 5% AND "
            "more than 20ms on at least one command -- per profiling-protocol.md, investigate "
            "the disagreement rather than averaging the instruments."
        )
        return 1
    print(
        "The harness's process_interval_seconds and an independent external timer "
        "(/usr/bin/time -v) agree on elapsed wall time within measurement noise on every "
        "comparable command. This does NOT by itself rule out a stdio-detached grandchild "
        "invisible to both mechanisms (see module docstring) -- child_cpu/wall above, from "
        "/usr/bin/time's rusage of every REAPED descendant, is the actual (partial) evidence "
        "the real candidate process trees were substantially waited-for."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
