#!/usr/bin/env python3
"""BP06: F057, instrumentation shifts runtime error line numbers,
against real gd-tools-cli 0.4.0.

Discovered during the BP06 corpus sweep (docs/benchmarks/corpus-run-
2026-09-19.md), verified independently here as its own fixture rather
than left as a note: gd-tools instruments a script by inserting tracker
call lines directly into its in-memory source_code string before
Script.reload(true) (coverage.gd's _inject_trackers()). Any runtime
error the ENGINE reports for that script afterward -- e.g. a division
by zero -- reports the line number in the INSTRUMENTED (tracker-
inserted) source, not the original source a developer is looking at.

This fixture isolates that fact with no debugger involved: a real
`gd-tools test --coverage` run produces a genuine plan.json for
subject.gd, then a standalone probe script (probe.gd, same F081-style
manual driver technique -- no GUT, no gd-tools CLI in this half) is run
twice against the SAME unmodified subject.gd: once with no
GD_TOOLS_COVERAGE_PLAN set (uninstrumented, reports the TRUE source
line via the engine's own SCRIPT ERROR diagnostic) and once with the
real plan.json from step one (instrumented, reports whatever line the
tracker insertion shifted the error to).

Scope: this is the engine-only half of "diagnostic accuracy under
instrumentation." Whether a debugger's breakpoint machinery is
similarly affected (binding to the wrong line, or the right line but
wrong reported state) is a DIFFERENT, unbuilt question -- tier-2 F082
("Original-source breakpoint") remains BP11's, and building F082 is
NOT a byproduct of this fixture. See oracles/F057.json's notes.

Run: python3 check.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GD_TOOLS_COVERAGE_SOURCE = REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage"

TRUE_ERROR_LINE = 4  # subject.gd's "return 100 / divisor" line, confirmed by cat -n

ERROR_LINE_RE = re.compile(r"at: run \(res://subject/subject\.gd:(\d+)\)")

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def run_probe(plan_path: Path | None) -> int | None:
    env = dict(os.environ)
    if plan_path is not None:
        env["GD_TOOLS_COVERAGE_PLAN"] = str(plan_path)
    result = subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--script", "probe.gd"],
        capture_output=True, text=True, timeout=30, env=env,
    )
    match = ERROR_LINE_RE.search(result.stderr)
    if match is None:
        check("probe_reports_a_run_line", False, f"stderr={result.stderr!r}")
        return None
    return int(match.group(1))


def main() -> int:
    for name, src in (("gut", GUT_SOURCE), ("gd-tools-coverage", GD_TOOLS_COVERAGE_SOURCE)):
        d = HERE / "addons" / name
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(src, d)

    for stale in (HERE / ".godot", HERE / ".gd-tools"):
        if stale.exists():
            shutil.rmtree(stale)

    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--import"],
        capture_output=True, timeout=60,
    )

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run(
        [str(GD_TOOLS_BIN), "test", "--coverage"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=60,
    )
    check("real_gd_tools_run_passed", "All 1 test(s) passed" in result.stdout, result.stdout)

    plan_path = HERE / ".gd-tools/coverage/plan.json"
    check("real_plan_json_produced", plan_path.exists(), "plan.json missing")

    uninstrumented_line = run_probe(plan_path=None)
    check("uninstrumented_probe_reports_true_source_line", uninstrumented_line == TRUE_ERROR_LINE,
          f"expected {TRUE_ERROR_LINE}, got {uninstrumented_line}")

    instrumented_line = run_probe(plan_path=plan_path)
    check("instrumented_probe_reports_a_line", instrumented_line is not None, "no line captured")
    if instrumented_line is not None and uninstrumented_line is not None:
        check(
            "instrumented_line_differs_from_true_source_line",
            instrumented_line != uninstrumented_line,
            f"expected instrumented line to differ from {uninstrumented_line}, both were {instrumented_line}",
        )
        check(
            "instrumented_line_is_shifted_forward_not_backward",
            instrumented_line > uninstrumented_line,
            f"expected instrumented line ({instrumented_line}) > true line ({uninstrumented_line}) "
            f"-- tracker insertion only ever adds lines above the target, never removes",
        )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        f"Confirmed against real gd-tools-cli 0.4.0: the same unmodified "
        f"subject.gd's division-by-zero reports line {TRUE_ERROR_LINE} "
        f"uninstrumented and a DIFFERENT, shifted line once gd-tools' real "
        f"plan.json is applied -- every engine diagnostic (SCRIPT ERROR, "
        f"assert failure location, print_stack()) from a covered run points "
        f"at the wrong line relative to the source a developer is reading."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
