#!/usr/bin/env python3
"""BP05: reproduce the godot-code-coverage incompatibility with Godot 4.7.1
against the F010 fixture (pilot/fixtures/oracles/F010.json's subject.gd,
unmodified).

Restores addons/gut from the one full committed copy, clears prior state,
runs the real GUT + godot-code-coverage pre/post hooks, and confirms:
tests still pass and the process exits 0, but coverage.gd fails to
compile (SCRIPT ERROR present in stderr) and no coverage_output.json is
ever written. See pilot/candidates/godot-code-coverage/PIN.md for the
full finding and upstream commit reference.

Run: python3 check.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    gut_dir = HERE / "addons" / "gut"
    if gut_dir.exists():
        shutil.rmtree(gut_dir)
    shutil.copytree(GUT_SOURCE, gut_dir)

    for stale in (HERE / ".godot", HERE / "coverage_output.json"):
        if stale.is_dir():
            shutil.rmtree(stale)
        elif stale.exists():
            stale.unlink()

    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--import"],
        capture_output=True, timeout=60,
    )

    result = subprocess.run(
        [
            str(GODOT_BIN), "--headless", "--path", str(HERE),
            "-s", "addons/gut/gut_cmdln.gd", "-gdir=res://tests", "-gexit",
        ],
        capture_output=True, text=True, timeout=30,
    )

    check("process_exit_code_zero", result.returncode == 0, f"exit={result.returncode}")
    check("tests_reported_passing", "All tests passed!" in result.stdout, result.stdout[-500:])
    check(
        "coverage_gd_fails_to_compile",
        "Cannot return value of type" in result.stderr and "coverage.gd" in result.stderr,
        result.stderr[:500],
    )
    check(
        "no_coverage_file_written",
        not (HERE / "coverage_output.json").exists(),
        "coverage_output.json exists despite the compile failure",
    )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed: godot-code-coverage's coverage.gd fails to compile on Godot 4.7.1 "
        "(NullCoverage return-type mismatch), silently -- tests still pass, exit code 0, "
        "no coverage_output.json is ever written."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
