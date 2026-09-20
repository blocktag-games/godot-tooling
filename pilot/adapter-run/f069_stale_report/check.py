#!/usr/bin/env python3
"""BP06: F069, stale report from an earlier run, against real
gd-tools-cli 0.4.0 + GUT v9.7.1.

Runs a real, successful `gd-tools test --coverage` to produce a genuine
plan.json/coverage.json bound to subject.gd's ORIGINAL source hash, then
modifies subject.gd (adding a function) WITHOUT re-running test or
--import -- exactly what a wrong-run/stale artifact looks like: real
coverage data, real source hash recorded inside it, but no longer
matching what's actually on disk. Confirms whether gd-tools' own
`coverage show`/`coverage report` (which read the stored plan/coverage
files directly, not a fresh test run) detect and reject this, or
silently present the stale numbers as current.

Run: python3 check.py
"""
from __future__ import annotations

import hashlib
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

ORIGINAL_SUBJECT = "extends RefCounted\n\nstatic func run() -> int:\n\treturn 1\n"
CHANGED_SUBJECT = (
    "extends RefCounted\n\n"
    "static func run() -> int:\n\treturn 1\n\n"
    "static func added_after_report_was_generated() -> int:\n\treturn 2\n"
)

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

    subject_path = HERE / "subject/subject.gd"
    subject_path.write_text(ORIGINAL_SUBJECT)

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

    plan = json.loads((HERE / ".gd-tools/coverage/plan.json").read_text())
    recorded_hash = plan["files"][0]["source_hash"]
    original_hash = "sha256:" + hashlib.sha256(ORIGINAL_SUBJECT.encode()).hexdigest()
    check("plan_records_original_source_hash", recorded_hash == original_hash, f"{recorded_hash} != {original_hash}")

    # Change the source WITHOUT re-running test or --import -- this is
    # what a stale artifact from an earlier run looks like: real data,
    # real recorded hash, no longer matching current disk state.
    subject_path.write_text(CHANGED_SUBJECT)
    current_hash = "sha256:" + hashlib.sha256(CHANGED_SUBJECT.encode()).hexdigest()
    check("source_on_disk_now_differs_from_recorded_hash", current_hash != recorded_hash, "test setup bug: hashes match")

    show_result = subprocess.run(
        [str(GD_TOOLS_BIN), "coverage", "show"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=30,
    )
    show_text = (show_result.stdout + show_result.stderr).lower()
    check("show_does_not_error", show_result.returncode == 0, f"exit={show_result.returncode}")
    check(
        "show_silently_presents_stale_numbers_with_no_warning",
        "mismatch" not in show_text and "hash" not in show_text and "out of date" not in show_text and "100.0%" in show_text,
        f"stdout={show_result.stdout!r} stderr={show_result.stderr!r}",
    )

    report_result = subprocess.run(
        [str(GD_TOOLS_BIN), "coverage", "report"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=30,
    )
    report_text = (report_result.stdout + report_result.stderr).lower()
    check("report_does_not_error", report_result.returncode == 0, f"exit={report_result.returncode}")
    check(
        "report_silently_writes_stale_report_with_no_warning",
        "mismatch" not in report_text and "hash" not in report_text and "out of date" not in report_text,
        f"stdout={report_result.stdout!r} stderr={report_result.stderr!r}",
    )

    subject_path.write_text(ORIGINAL_SUBJECT)
    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: 'coverage show' and 'coverage "
        "report' both read the stored plan.json/coverage.json directly and neither "
        "checks the recorded source_hash against the current file on disk -- a "
        "stale report from before a source change is presented as current with no "
        "warning, satisfying what looks like a fresh coverage check for source "
        "that no longer matches."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
