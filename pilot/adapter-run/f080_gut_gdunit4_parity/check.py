#!/usr/bin/env python3
"""BP06: F080, GUT and GdUnit4 parity, against real GUT v9.7.1 and
GdUnit4 v6.2.1 on the pinned Godot 4.7.1 engine.

Two separate projects (project_gut, project_gdunit4) share the exact
same subject.gd. Each has its own thin test wrapper (GUT's GutTest vs.
GdUnit4's GdUnitTestSuite) that calls subject.gd:run() with the SAME
two inputs and writes an event trace to its own user://trace.json --
not stdout, since the two runners format console output very
differently and diffing that would compare runner noise, not
application behavior.

The discriminating assertion: the two trace files' CONTENT is byte-for-
byte identical (after generation timestamps, which neither trace even
has here) -- proving the thin drivers invoke identical application
behavior, independent of which test framework drives them.

This fixture does NOT establish gd-tools coverage parity across
runners -- gd-tools' coverage collection is bound to GUT's hook system
(pre_run_hook.gd/post_run_hook.gd), so a GdUnit4 run produces no
gd-tools coverage data at all. See oracles/F080.json's ambiguities.

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
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GDUNIT4_SOURCE = REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4"

GUT_PROJECT = HERE / "project_gut"
GDUNIT4_PROJECT = HERE / "project_gdunit4"
GUT_USERDATA = Path.home() / ".local/share/godot/app_userdata/f080-gut-gdunit4-parity-gut"
GDUNIT4_USERDATA = Path.home() / ".local/share/godot/app_userdata/f080-gut-gdunit4-parity-gdunit4"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    for d in (GUT_USERDATA, GDUNIT4_USERDATA):
        if d.exists():
            shutil.rmtree(d)

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)

    # --- GUT run ---
    addon_dir = GUT_PROJECT / "addons" / "gut"
    if addon_dir.exists():
        shutil.rmtree(addon_dir)
    shutil.copytree(GUT_SOURCE, addon_dir)
    shutil.rmtree(GUT_PROJECT / ".godot", ignore_errors=True)
    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(GUT_PROJECT), "--import"],
        capture_output=True, timeout=60,
    )
    gut_result = subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(GUT_PROJECT),
         "-s", "addons/gut/gut_cmdln.gd", "-gdir=res://test", "-gexit"],
        cwd=str(GUT_PROJECT), env=env, capture_output=True, text=True, timeout=60,
    )
    check("gut_run_passed", "All tests passed" in gut_result.stdout, gut_result.stdout[-600:])
    shutil.rmtree(GUT_PROJECT / ".godot", ignore_errors=True)

    # --- GdUnit4 run ---
    addon_dir = GDUNIT4_PROJECT / "addons" / "gdUnit4"
    if addon_dir.exists():
        shutil.rmtree(addon_dir)
    shutil.copytree(GDUNIT4_SOURCE, addon_dir)
    for stale in (GDUNIT4_PROJECT / ".godot", GDUNIT4_PROJECT / "reports"):
        if stale.exists():
            shutil.rmtree(stale)
    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(GDUNIT4_PROJECT), "--import"],
        capture_output=True, timeout=60,
    )
    gdunit4_result = subprocess.run(
        ["bash", "addons/gdUnit4/runtest.sh", "-a", "test"],
        cwd=str(GDUNIT4_PROJECT), env=env, capture_output=True, text=True, timeout=60,
    )
    check(
        "gdunit4_run_passed",
        "1 test cases" in gdunit4_result.stdout and "0 failures" in gdunit4_result.stdout,
        gdunit4_result.stdout[-800:],
    )
    shutil.rmtree(GDUNIT4_PROJECT / ".godot", ignore_errors=True)
    shutil.rmtree(GDUNIT4_PROJECT / "reports", ignore_errors=True)

    # --- Compare traces ---
    gut_trace_path = GUT_USERDATA / "trace.json"
    gdunit4_trace_path = GDUNIT4_USERDATA / "trace.json"
    check("gut_trace_written", gut_trace_path.exists(), str(gut_trace_path))
    check("gdunit4_trace_written", gdunit4_trace_path.exists(), str(gdunit4_trace_path))

    if gut_trace_path.exists() and gdunit4_trace_path.exists():
        gut_trace = gut_trace_path.read_text()
        gdunit4_trace = gdunit4_trace_path.read_text()
        check(
            "traces_byte_identical_across_runners",
            gut_trace == gdunit4_trace,
            f"gut={gut_trace!r} gdunit4={gdunit4_trace!r}",
        )

    for d in (GUT_USERDATA, GDUNIT4_USERDATA):
        if d.exists():
            shutil.rmtree(d)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real GUT v9.7.1 and GdUnit4 v6.2.1: two thin test "
        "drivers, one per runner, produce a byte-identical event trace for the "
        "SAME subject.gd and the SAME inputs -- the choice of test framework "
        "does not alter application behavior."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
