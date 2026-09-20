#!/usr/bin/env python3
"""BP06: F075, source restoration, against real gd-tools-cli 0.4.0 +
GUT v9.7.1.

Runs a real gd-tools test --coverage with two tests, one passing and
one DELIBERATELY failing, and confirms subject.gd on disk is byte-for-
byte unchanged afterward, for both outcomes. gd-tools instruments via
GDScript's in-memory Script.reload(true), not by rewriting source files
in place, so this is expected to hold regardless of test outcome --
this fixture makes that expectation a checked, reproducible fact rather
than an assumption.

Run: python3 check.py
"""
from __future__ import annotations

import hashlib
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


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    hash_before = sha256_of(subject_path)

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
    check("run_had_one_pass_and_one_deliberate_failure", "1 failed, 1 passed" in result.stdout, result.stdout)

    hash_after = sha256_of(subject_path)
    check(
        "source_unchanged_on_disk_after_mixed_pass_fail_run",
        hash_before == hash_after,
        f"before={hash_before} after={hash_after}",
    )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: subject.gd's "
        "source is byte-for-byte unchanged on disk after a real coverage run, "
        "including a run that contains a deliberately failing test -- "
        "instrumentation is in-memory only, source restoration is not something "
        "gd-tools 0.4.0 needs to do because it never mutates the file."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
