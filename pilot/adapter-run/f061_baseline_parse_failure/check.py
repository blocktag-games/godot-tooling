#!/usr/bin/env python3
"""BP06: F061, baseline parse failure, against real gd-tools-cli 0.4.0
+ GUT v9.7.1.

subject.gd is deliberately invalid GDScript (an incomplete expression --
a real syntax error, not a runtime bug). Confirms the failure is
attributed explicitly to the SOURCE's own parse error, not silently
treated as a collector/coverage-tool defect: gd-tools must skip the
broken file from its coverage plan with an explicit diagnostic (not
crash or silently include it), and the overall run must fail with a
nonzero exit code and a clear GDScript-level parse error in the output.

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
    combined = result.stdout + result.stderr

    check("run_exits_nonzero", result.returncode != 0, f"exit={result.returncode}")
    check(
        "failure_attributed_to_a_real_gdscript_parse_error",
        "Parse Error" in combined and "Expected expression" in combined,
        "expected a real engine-level parse error message in the output",
    )
    check(
        "gd_tools_explicitly_skips_the_broken_file_from_coverage",
        "syntax error prevents coverage parsing" in combined,
        "expected gd-tools' own explicit skip-with-reason diagnostic",
    )

    coverage_path = HERE / ".gd-tools/coverage/coverage.json"
    if coverage_path.exists():
        coverage = json.loads(coverage_path.read_text())
        check(
            "broken_file_not_silently_counted_as_covered",
            len(coverage.get("files", [])) == 0,
            f"expected zero files in coverage.json, got {coverage.get('files')}",
        )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: an invalid "
        "(unparseable) fixture is not scored as a collector defect -- gd-tools "
        "explicitly skips the broken file with a named reason, the underlying "
        "engine parse error is visible verbatim in the output, and the run fails "
        "with a nonzero exit code, all without gd-tools itself crashing or "
        "silently marking anything covered."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
