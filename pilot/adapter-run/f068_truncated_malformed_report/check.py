#!/usr/bin/env python3
"""BP06: F068, truncated/malformed coverage report, against real
gd-tools-cli 0.4.0 + GUT v9.7.1.

Runs a real, successful `gd-tools test --coverage` to produce a genuine
coverage.json, truncates it in half (a realistic corruption -- e.g. a
process killed mid-write), then confirms that BOTH of gd-tools' own
consumers of that file (`coverage show` and `coverage report`) reject it
explicitly rather than silently treating it as zero or complete
coverage.

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
    check("initial_run_passed", "All 1 test(s) passed" in result.stdout, result.stdout)

    coverage_path = HERE / ".gd-tools/coverage/coverage.json"
    original_bytes = coverage_path.read_bytes()
    check("coverage_json_produced", coverage_path.exists() and len(original_bytes) > 0, "coverage.json missing or empty")

    truncated = original_bytes[: len(original_bytes) // 2]
    coverage_path.write_bytes(truncated)
    try:
        json.loads(truncated)
        truly_malformed = False
    except json.JSONDecodeError:
        truly_malformed = True
    check("truncated_bytes_are_genuinely_invalid_json", truly_malformed, "truncation happened to still be valid JSON -- adjust the cut point")

    show_result = subprocess.run(
        [str(GD_TOOLS_BIN), "coverage", "show"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=30,
    )
    check("show_exits_nonzero_on_malformed_report", show_result.returncode != 0, f"exit={show_result.returncode}")
    check(
        "show_reports_invalid_json_explicitly_not_zero_coverage",
        "invalid json" in (show_result.stdout + show_result.stderr).lower(),
        f"stdout={show_result.stdout!r} stderr={show_result.stderr!r}",
    )

    report_result = subprocess.run(
        [str(GD_TOOLS_BIN), "coverage", "report"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=30,
    )
    check("report_exits_nonzero_on_malformed_report", report_result.returncode != 0, f"exit={report_result.returncode}")
    check(
        "report_reports_invalid_json_explicitly_not_complete_coverage",
        "invalid json" in (report_result.stdout + report_result.stderr).lower(),
        f"stdout={report_result.stdout!r} stderr={report_result.stderr!r}",
    )

    coverage_path.write_bytes(original_bytes)
    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: a truncated coverage.json is "
        "rejected explicitly by both 'coverage show' and 'coverage report' (nonzero "
        "exit, explicit 'Invalid JSON' diagnostic), never silently read as zero or "
        "complete coverage."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
