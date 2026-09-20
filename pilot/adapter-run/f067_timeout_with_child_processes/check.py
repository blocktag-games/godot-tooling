#!/usr/bin/env python3
"""BP06: F067, timeout with child processes, against real gd-tools-cli
0.4.0 + GUT v9.7.1.

tests/test_subject.gd is deliberately slow (OS.delay_msec(15000)) so a
short harness-level timeout has a real window to fire while the Godot
child process gd-tools spawns is still genuinely running. Confirms
pilot/harness/runner.run() terminates the ENTIRE process tree it owns
on timeout, not just the direct child (gd-tools itself) -- a real
defect, found and fixed while building this fixture: a plain
subprocess.run(..., timeout=...) only ever signals the direct child;
a grandchild the child spawned (Godot, spawned BY gd-tools) is left
orphaned and running with no owner left to reap it.

Run: python3 check.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GD_TOOLS_COVERAGE_SOURCE = REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage"

sys.path.insert(0, str(REPO_ROOT / "pilot/harness"))
from runner import run  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def godot_processes_for_this_project() -> list[int]:
    """Find PIDs of any Godot process whose command line references this
    fixture's own path -- avoids false positives from Godot processes
    other fixtures or the user's own session might have running.
    """
    result = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True)
    pids = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid_str, cmdline = parts
        if "Godot_v4.7.1" in cmdline and str(HERE) in cmdline:
            pids.append(int(pid_str))
    return pids


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

    check("no_godot_process_running_before_test", godot_processes_for_this_project() == [], "a stale process from a prior run is already running")

    os.environ["GODOT_BIN"] = str(GODOT_BIN)
    # The test itself takes >=15s (OS.delay_msec(15000)); a 3s harness
    # timeout is guaranteed to fire while the Godot child is still
    # genuinely running, not racing a fast-exiting process.
    result = run([str(GD_TOOLS_BIN), "test", "--coverage"], cwd=str(HERE), timeout_s=3.0)
    check("harness_reports_timeout", result.timed_out, str(result))

    # Give the OS a brief moment to finish reaping after SIGKILL before
    # checking -- ps can lag a killed process by a few milliseconds.
    deadline = time.monotonic() + 2.0
    orphans = godot_processes_for_this_project()
    while orphans and time.monotonic() < deadline:
        time.sleep(0.1)
        orphans = godot_processes_for_this_project()

    check(
        "godot_child_process_terminated_not_orphaned",
        orphans == [],
        f"orphaned Godot process(es) still running after harness timeout: {orphans}",
    )

    shutil.rmtree(HERE / ".godot", ignore_errors=True)
    shutil.rmtree(HERE / ".gd-tools", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: pilot/harness/"
        "runner.run()'s timeout terminates the entire process tree it owns -- "
        "the Godot process gd-tools spawns is killed along with gd-tools itself, "
        "not left running as an orphan. (A prior version of run(), using plain "
        "subprocess.run(..., timeout=...), left exactly this orphan -- fixed in "
        "the same commit as this fixture.)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
