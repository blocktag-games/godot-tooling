#!/usr/bin/env python3
"""BP06: F005, loaded dependency outside selection, against real
gd-tools-cli 0.4.0 + GUT v9.7.1.

subject/app.gd (selected) preloads and calls addons/vendor_lib/vendor.gd
(excluded by default -- addons/ is in gd-tools' DEFAULT_EXCLUDES).
Confirms real execution of excluded code neither broadens the plan
(vendor.gd sneaking in because it actually ran) nor breaks measurement
of the file that IS selected.

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
    result = subprocess.run(
        [str(GD_TOOLS_BIN), "test", "--coverage"],
        cwd=str(HERE), env=env, capture_output=True, text=True, timeout=60,
    )
    check("exit_code_zero", result.returncode == 0, f"exit={result.returncode}\n{result.stdout}")
    check("test_passed", "All 1 test(s) passed" in result.stdout, result.stdout)

    plan = json.loads((HERE / ".gd-tools/coverage/plan.json").read_text())
    paths = {f["path"] for f in plan["files"]}
    check("only_app_gd_in_plan", paths == {"res://subject/app.gd"}, str(paths))

    coverage = json.loads((HERE / ".gd-tools/coverage/coverage.json").read_text())
    app_file = plan["files"][0]
    id_to_line = {e["id"]: e["line"] for e in app_file["lines"]}
    hits_by_line = {id_to_line[int(k)]: v for k, v in coverage["files"][0]["hits"].items()}
    check("app_gd_line_6_hit", hits_by_line.get(6, 0) > 0, str(hits_by_line))

    shutil.rmtree(HERE / ".godot", ignore_errors=True)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 + GUT v9.7.1: calling excluded "
        "vendor.gd from selected app.gd neither broadens the plan (vendor.gd stays "
        "absent) nor breaks measurement of app.gd itself."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
