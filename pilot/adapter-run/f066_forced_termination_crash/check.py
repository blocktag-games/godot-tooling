#!/usr/bin/env python3
"""BP06: F066, forced termination or crash, against real gd-tools-cli
0.4.0 + GUT v9.7.1.

tests/test_subject.gd is deliberately slow (OS.delay_msec(15000)) so
this script has a real window to find the Godot process gd-tools
spawned and SIGKILL it directly -- simulating an external crash or
OOM-kill, not a graceful interruption gd-tools itself could catch and
handle (that would be a different, easier case). Confirms:

1. Whatever partial evidence exists after the crash is explicit, not
   fabricated: plan.json (written before the run starts) is present,
   but coverage.json and results.xml (both written only when the run
   completes normally) are absent -- not corrupted, not zero, simply
   missing, which is the correct signal for "we don't know what
   happened" per F001/F003's established "unknown differs from
   measured zero" convention.
2. gd-tools' own wrapper reports the crash honestly (the real exit
   code, e.g. -9 for SIGKILL) rather than silently treating a missing
   JUnit report as success.
3. A completely fresh run afterward, without any manual cleanup of the
   crashed run's leftover plan.json, succeeds normally -- recovery
   requires no special handling.

Run: python3 check.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
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


def find_godot_pid_for_this_project(timeout_s: float = 20.0) -> int | None:
    """Poll for the real GUT test-run Godot process (not the earlier
    --import step) by matching its command line against this fixture's
    own path AND the gut_cmdln.gd entry point.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        result = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True)
        for line in result.stdout.splitlines()[1:]:
            parts = line.strip().split(None, 1)
            if len(parts) != 2:
                continue
            pid_str, cmdline = parts
            if "Godot_v4.7.1" in cmdline and str(HERE) in cmdline and "gut_cmdln.gd" in cmdline:
                return int(pid_str)
        time.sleep(0.2)
    return None


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

    # Launch the (slow) real test run in the background so this script
    # can find and kill its Godot process mid-run, from the outside --
    # simulating an OOM-kill or an operator `kill -9`, not something
    # gd-tools could catch and handle gracefully itself.
    proc = subprocess.Popen(
        [str(GD_TOOLS_BIN), "test", "--coverage"],
        cwd=str(HERE), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    godot_pid = find_godot_pid_for_this_project(timeout_s=25.0)
    check("found_running_godot_test_process", godot_pid is not None, "gd-tools' Godot test process never appeared")

    if godot_pid is not None:
        os.kill(godot_pid, 9)

    gd_tools_stdout, gd_tools_stderr = proc.communicate(timeout=30)
    check(
        "gd_tools_reports_real_crash_exit_code_honestly",
        "Godot exit code: -9" in gd_tools_stderr,
        f"stdout={gd_tools_stdout!r} stderr={gd_tools_stderr!r}",
    )
    check(
        "gd_tools_does_not_fabricate_a_result",
        "All" not in gd_tools_stdout and "passed" not in gd_tools_stdout,
        f"stdout={gd_tools_stdout!r}",
    )

    plan_path = HERE / ".gd-tools/coverage/plan.json"
    coverage_path = HERE / ".gd-tools/coverage/coverage.json"
    results_path = HERE / ".gd-tools/results.xml"
    check("plan_json_present_written_before_run_started", plan_path.exists(), "plan.json missing -- unexpected, it's written before the test even runs")
    check("coverage_json_absent_not_fabricated", not coverage_path.exists(), "coverage.json exists despite the crash -- it should only be written by post_run_hook.gd on normal completion")
    check("results_xml_absent_not_fabricated", not results_path.exists(), "results.xml exists despite the crash")

    # Recovery: a completely fresh run, with no manual cleanup of the
    # crashed run's leftover plan.json, must succeed normally.
    recovery_result = subprocess.run(
        [str(GD_TOOLS_BIN), "test", "--coverage"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=60,
    )
    check("recovery_run_exits_zero", recovery_result.returncode == 0, recovery_result.stdout)
    check("recovery_run_test_passed", "All 1 test(s) passed" in recovery_result.stdout, recovery_result.stdout)
    check("recovery_run_produced_coverage_json", coverage_path.exists(), "coverage.json still missing after a clean recovery run")

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: a forced "
        "SIGKILL of the Godot process leaves only the evidence written before "
        "the crash (plan.json), with no fabricated coverage.json or JUnit "
        "report -- gd-tools reports the real crash exit code honestly. A fresh "
        "run afterward, with no manual cleanup, recovers and succeeds normally."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
