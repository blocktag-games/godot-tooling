#!/usr/bin/env python3
"""BP05 follow-up / BP06 precursor: Nano Coverage's GdUnit4 integration
(not the raw ProjectBootstrapper API that crashed in
pilot/adapter-run/nano-coverage-f010_straight_line/) against F010's
unmodified subject.gd.

Requires the Nano Coverage extension to already be built (see
pilot/candidates/nano-coverage-godot-PIN.md) with both .so naming
variants present (the "lib"-prefixed one SCons produces, and the
unprefixed one the checked-in .gdextension file expects).

Run: python3 check.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GDUNIT4_SOURCE = REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4"
NANO_ADDON_SOURCE = REPO_ROOT / "pilot/candidates/nano-coverage-godot/demo/addons/nano_coverage_godot"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    if not NANO_ADDON_SOURCE.exists():
        print(f"SKIP: Nano Coverage not built at {NANO_ADDON_SOURCE}. See nano-coverage-godot-PIN.md to build it.")
        return 2

    for name in ("gdUnit4", "nano_coverage_godot"):
        d = HERE / "addons" / name
        if d.exists():
            shutil.rmtree(d)
    shutil.copytree(GDUNIT4_SOURCE, HERE / "addons" / "gdUnit4")
    shutil.copytree(NANO_ADDON_SOURCE, HERE / "addons" / "nano_coverage_godot")

    for stale in (HERE / ".godot", HERE / "reports", HERE / "coverage-data", HERE / "coverage-report"):
        if stale.exists():
            shutil.rmtree(stale)

    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--import"],
        capture_output=True, timeout=60,
    )

    import os
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run(
        ["bash", "addons/gdUnit4/runtest.sh", "-a", "test"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=60,
    )

    check("exit_code_zero", result.returncode == 0, f"exit={result.returncode}")
    check("no_crash", "Cannot call method" not in result.stdout, result.stdout[-500:])

    lcov = HERE / "coverage-report" / "lcov.info"
    check("lcov_report_generated", lcov.exists(), "coverage-report/lcov.info missing")
    if lcov.exists():
        content = lcov.read_text()
        check(
            "correct_line_hits_for_subject",
            "SF:subject/subject.gd" in content
            and "DA:4,1" in content
            and "DA:5,1" in content
            and "DA:6,1" in content,
            content,
        )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)
    shutil.rmtree(HERE / "reports", ignore_errors=True)
    shutil.rmtree(HERE / "coverage-data", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Nano Coverage's GdUnit4 session hook correctly instruments and reports "
        "F010's subject.gd on Godot 4.7.1 -- unlike the raw ProjectBootstrapper "
        "API example, which crashes (see nano-coverage-f010_straight_line/)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
