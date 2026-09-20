#!/usr/bin/env python3
"""BP05: reproduce GdUnit4 v6.2.1 running F010's fixture on Godot 4.7.1.

Run: python3 check.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GDUNIT4_SOURCE = REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    addon_dir = HERE / "addons" / "gdUnit4"
    if addon_dir.exists():
        shutil.rmtree(addon_dir)
    shutil.copytree(GDUNIT4_SOURCE, addon_dir)

    for stale in (HERE / ".godot", HERE / "reports"):
        if stale.exists():
            shutil.rmtree(stale)

    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--import"],
        capture_output=True, timeout=60,
    )

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run(
        ["bash", "addons/gdUnit4/runtest.sh", "-a", "test"],
        cwd=str(HERE),
        env=env,
        capture_output=True, text=True, timeout=60,
    )

    check("exit_code_zero", result.returncode == 0, f"exit={result.returncode}")
    check("one_test_case_passed", "1 test cases" in result.stdout and "0 failures" in result.stdout, result.stdout[-800:])

    shutil.rmtree(HERE / ".godot", ignore_errors=True)
    shutil.rmtree(HERE / "reports", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print("GdUnit4 v6.2.1 runs F010's fixture correctly on Godot 4.7.1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
