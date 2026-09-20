#!/usr/bin/env python3
"""BP06: F063, application test failure, against real gd-tools-cli
0.4.0 + GUT v9.7.1.

subject.gd has a genuine application bug (returns 2, not 1); the test
correctly asserts the intended behavior and therefore fails. Confirms
coverage completeness is independent of test outcome: the line that DID
execute (the buggy return statement) must still be reported as covered,
exactly as it would be for a passing test -- a failing assertion must
never zero out or otherwise degrade the coverage measurement for the
code that actually ran.

Run: python3 check.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GD_TOOLS_COVERAGE_SOURCE = REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


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

    check("test_run_exits_nonzero", result.returncode != 0, f"exit={result.returncode}")
    check("test_actually_failed_on_the_real_assertion", "expected to equal" in result.stdout, result.stdout)
    check("failure_is_an_application_bug_not_a_crash", "SCRIPT ERROR" not in result.stdout and "SCRIPT ERROR" not in result.stderr, "expected a clean assertion failure, not an engine error")

    plan = json.loads((HERE / ".gd-tools/coverage/plan.json").read_text())
    coverage = json.loads((HERE / ".gd-tools/coverage/coverage.json").read_text())
    check("plan_still_tracks_the_file_despite_test_failure", len(plan["files"]) == 1, str(plan))

    id_to_line = {e["id"]: e["line"] for e in plan["files"][0]["lines"]}
    hits_by_line = {id_to_line[int(k)]: v for k, v in coverage["files"][0]["hits"].items()}
    check(
        "buggy_return_line_still_reported_as_covered",
        hits_by_line.get(4, 0) > 0,
        f"expected line 4 (the buggy return statement, which DID execute) hit despite the test failing, got {hits_by_line}",
    )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: a failing "
        "assertion (a real application bug) does not degrade coverage "
        "measurement -- the line that executed is still reported as covered, "
        "exactly as it would be for a passing test. Coverage completeness and "
        "test outcome are independent facts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
