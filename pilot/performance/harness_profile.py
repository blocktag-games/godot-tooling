#!/usr/bin/env python3
"""BP08: "one useful script/native/harness capture where available"
(implementation-plan.md's BP08 row). Native Linux `perf` was already
confirmed unavailable in this session (not installed, kernel
`perf_event_paranoid=3`, no sudo) -- see docs/benchmarks/
implementation-plan.md's "Profiler access/build effort" row. Godot's
built-in profiler and a Tracy-instrumented build were not validated
this session either (no debug-server automation set up, no Tracy
build). What IS available without any of that: Python's own `cProfile`
against the HARNESS's Python-side orchestration itself -- per
profiling-protocol.md's layer table ("Python orchestration... cProfile
and optional py-spy... process launch, polling, log handling,
serialization, hashing, normalization, and report generation").

This captures where run_condition.py's OWN Python code (not the child
Godot/gd-tools/GdUnit4 process, which cProfile cannot see inside)
spends time across one real condition run -- confirming the harness's
own CPU work is negligible relative to the timed child-process
interval, and demonstrating capture feasibility/cost for a native or
script profiler generally.

Per docs/benchmarks/implementation-plan.md's storage note ("Record
bytes per capture in BP08, estimate the planned total plus retention
headroom, and choose a versioned archive before the main study"): this
script also records the resulting .prof file's size and extrapolates
total storage IF every main-study run were profiled this way (not a
recommendation to actually do so -- profiling every run would itself
be an observer-effect confound; this is a cost estimate only).

Run: python3 harness_profile.py
"""
from __future__ import annotations

import cProfile
import io
import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS
from run_condition import run_condition

OUT_PROF = Path(__file__).parent / "harness_profile_w01_b0.prof"


def main() -> int:
    profiler = cProfile.Profile()
    profiler.enable()
    result = run_condition(GD_TOOLS, "w01", "B0", scratch_label="bp08-harness-profile")
    profiler.disable()

    if not result.behavior_ok:
        print(f"FAIL: profiled run itself did not pass its behavior check -- capture is not meaningful.\n{result.stdout}", file=sys.stderr)
        return 1

    profiler.dump_stats(str(OUT_PROF))
    prof_bytes = OUT_PROF.stat().st_size

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(15)
    print(stream.getvalue())

    # cProfile cannot see inside the child Godot/gd-tools process -- it
    # only measures run_condition()'s OWN Python-side work (scratch
    # setup, env dict construction, safe_run's bookkeeping around
    # Popen/communicate, stdout string scanning, JSON parsing for the
    # coverage-artifact check). The child process's wall time dominates
    # this function's own total by construction (safe_run blocks on
    # communicate()), so a large gap between "total time in this
    # function" and "time NOT attributable to Popen/communicate" is
    # exactly the harness's own measurable overhead.
    print(f"Total condition wall time: {result.process_interval_seconds:.4f}s")
    print(f"Profile artifact: {OUT_PROF} ({prof_bytes} bytes)")

    main_study_runs = 1200  # from pilot_report.py's cost extrapolation (10 sessions x 6 blocks, 8 cells)
    projected_bytes = prof_bytes * main_study_runs
    print(
        f"\nStorage estimate IF every main-study run were profiled this way: "
        f"{prof_bytes} bytes/run x {main_study_runs} runs = {projected_bytes / 1_048_576:.1f} MiB "
        f"(not recommended as a default -- profiling every run is itself an observer-effect "
        f"confound per profiling-protocol.md's factorial P factor; this is a feasibility/cost "
        f"estimate only, for sizing a versioned archive IF selected main-study cells are profiled)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
