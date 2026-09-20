#!/usr/bin/env python3
"""BP06: F081, standalone/manual driver, against real gd-tools-cli
0.4.0 (coverage collection) with NO test framework involved at all in
the second half of this check.

Step 1: a real `gd-tools test --coverage` run via GUT produces the
REFERENCE coverage.json for two calls (run(3), run(0)).

Step 2: a from-scratch manual_driver.gd -- no GUT, no gd-tools CLI,
just the raw `_GDTCoverage` autoload plus hand-written glue replicating
pre_run_hook.gd (set_active(true)) and post_run_hook.gd (get_hits() ->
JSON) -- drives the SAME two calls against the SAME plan.json.

The discriminating assertion: the manually-produced coverage.json's
hits are EXACTLY EQUAL to the GUT-path reference, not merely
"nonempty" or "plausible." Equality is what proves coverage collection
is genuinely independent of any test framework, not just usable without
one in some degraded sense.

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

    # Step 1: real GUT-path reference.
    result = subprocess.run(
        [str(GD_TOOLS_BIN), "test", "--coverage"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=60,
    )
    check("reference_gut_run_passed", "All 2 test(s) passed" in result.stdout, result.stdout)

    reference_plan = json.loads((HERE / ".gd-tools/coverage/plan.json").read_text())
    reference_coverage = json.loads((HERE / ".gd-tools/coverage/coverage.json").read_text())
    reference_hits = reference_coverage["files"][0]["hits"]

    plan_path = HERE / "reference_plan.json"
    plan_path.write_text(json.dumps(reference_plan))
    manual_output = HERE / "manual_coverage.json"
    if manual_output.exists():
        manual_output.unlink()

    # Reset .godot so the manual run starts from the same cold-import
    # state as the reference run did, not reusing its live process.
    shutil.rmtree(HERE / ".godot", ignore_errors=True)
    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--import"],
        capture_output=True, timeout=60,
    )

    # Step 2: manual driver, no GUT, no gd-tools CLI -- just the plan
    # env var and a from-scratch script.
    manual_env = dict(os.environ)
    manual_env["GD_TOOLS_COVERAGE_PLAN"] = str(plan_path)
    manual_result = subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--script", "tests/manual_driver.gd", "--", str(manual_output)],
        cwd=str(HERE), env=manual_env, capture_output=True, text=True, timeout=30,
    )
    check("manual_driver_exits_zero", manual_result.returncode == 0, manual_result.stdout + manual_result.stderr)
    check("manual_coverage_json_produced", manual_output.exists(), "manual_coverage.json was not written")

    if manual_output.exists():
        manual_coverage = json.loads(manual_output.read_text())
        manual_hits = manual_coverage["files"][0]["hits"]
        check(
            "manual_driver_hits_exactly_equal_gut_reference",
            manual_hits == reference_hits,
            f"reference={reference_hits} manual={manual_hits}",
        )
        manual_output.unlink()

    plan_path.unlink()
    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: a from-scratch manual "
        "driver with no GUT and no gd-tools CLI involved -- just the raw "
        "_GDTCoverage autoload plus ~15 lines of hand-written glue replicating "
        "pre_run_hook.gd/post_run_hook.gd -- produces coverage data EXACTLY "
        "equal to the real GUT-path artifact for the same execution. "
        "Coverage collection is genuinely independent of any test framework."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
