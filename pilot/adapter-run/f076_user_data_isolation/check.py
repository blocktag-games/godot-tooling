#!/usr/bin/env python3
"""BP06: F076, user-data isolation, against real gd-tools-cli 0.4.0 +
GUT v9.7.1.

Two separate, differently-named projects (project_a, project_b) each
write a unique sentinel file to user:// during their own test run.
Confirms each run's sentinel lands only in that project's own
app_userdata directory (Godot resolves user:// per config/name by
default) -- neither run reads, consumes, or leaks into the other's
profile.

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
GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GD_TOOLS_COVERAGE_SOURCE = REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage"

APP_USERDATA = Path.home() / ".local/share/godot/app_userdata"
PROJECT_NAMES = {"a": "f076-user-data-isolation-a", "b": "f076-user-data-isolation-b"}

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    for label in PROJECT_NAMES:
        userdata_dir = APP_USERDATA / PROJECT_NAMES[label]
        if userdata_dir.exists():
            shutil.rmtree(userdata_dir)

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)

    for label in ("a", "b"):
        project_dir = HERE / f"project_{label}"
        for name, src in (("gut", GUT_SOURCE), ("gd-tools-coverage", GD_TOOLS_COVERAGE_SOURCE)):
            d = project_dir / "addons" / name
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(src, d)
        for stale in (project_dir / ".godot", project_dir / ".gd-tools"):
            if stale.exists():
                shutil.rmtree(stale)
        subprocess.run(
            [str(GODOT_BIN), "--headless", "--path", str(project_dir), "--import"],
            capture_output=True, timeout=60,
        )
        result = subprocess.run(
            [str(GD_TOOLS_BIN), "test", "--coverage"],
            cwd=str(project_dir), env=env, capture_output=True, text=True, timeout=60,
        )
        check(f"project_{label}_test_passed", "All 1 test(s) passed" in result.stdout, result.stdout)
        shutil.rmtree(project_dir / ".godot", ignore_errors=True)

    sentinel_a = APP_USERDATA / PROJECT_NAMES["a"] / "sentinel_a.txt"
    sentinel_b = APP_USERDATA / PROJECT_NAMES["b"] / "sentinel_b.txt"
    cross_a_in_b = APP_USERDATA / PROJECT_NAMES["b"] / "sentinel_a.txt"
    cross_b_in_a = APP_USERDATA / PROJECT_NAMES["a"] / "sentinel_b.txt"

    check("project_a_own_sentinel_present", sentinel_a.exists(), str(sentinel_a))
    check("project_b_own_sentinel_present", sentinel_b.exists(), str(sentinel_b))
    check("project_a_sentinel_not_leaked_into_b", not cross_a_in_b.exists(), str(cross_a_in_b))
    check("project_b_sentinel_not_leaked_into_a", not cross_b_in_a.exists(), str(cross_b_in_a))
    if sentinel_a.exists():
        check("project_a_sentinel_content_correct", sentinel_a.read_text() == "sentinel_from_project_a", sentinel_a.read_text())
    if sentinel_b.exists():
        check("project_b_sentinel_content_correct", sentinel_b.read_text() == "sentinel_from_project_b", sentinel_b.read_text())

    for label in PROJECT_NAMES:
        userdata_dir = APP_USERDATA / PROJECT_NAMES[label]
        if userdata_dir.exists():
            shutil.rmtree(userdata_dir)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: two "
        "differently-named projects' test runs write to and read from "
        "completely separate user:// profiles, with no leakage or consumption "
        "of the other project's data in either direction."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
