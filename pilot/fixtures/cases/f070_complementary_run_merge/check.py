#!/usr/bin/env python3
"""BP06 ground-truth check for F070 against the real, pinned
gd-tools-cli 0.4.0.

subject.gd has an if/else where each branch's body sits on a different
line (line 5: taken when flag=true, line 6: taken when flag=false, plus
the if-header's own branch obligation at line 4). run_true.json and
run_false.json are two hand-crafted coverage-data files modeling two
COMPLEMENTARY runs -- each covers a disjoint subset of the file's
tracked lines/branches. Confirms `gd-tools coverage merge` produces
exactly the union: every line/branch either run touched is present with
its own run's count, and nothing either run didn't touch is invented.

Run: python3 check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
GD_TOOLS_VENV = HERE.parent.parent.parent / "gd-tools"
sys.path.insert(0, str(GD_TOOLS_VENV / ".venv/lib/python3.13/site-packages"))

from gd_tools.coverage.plan_generator import generate_plan  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    plan = generate_plan(str(HERE / "project"))
    ids_by_line = {fp.line: fp.id for fp in plan.files[0].lines}
    print(f"plan lines->ids: {ids_by_line}")
    check(
        "plan_has_the_three_expected_lines",
        set(ids_by_line) == {4, 5, 6},
        str(ids_by_line),
    )

    gd_tools_bin = str(GD_TOOLS_VENV / ".venv/bin/gd-tools")
    merged_path = HERE / "project" / "merged.json"
    result = subprocess.run(
        [
            gd_tools_bin, "coverage", "merge",
            str(HERE / "project" / "run_true.json"),
            str(HERE / "project" / "run_false.json"),
            "--output", str(merged_path),
        ],
        cwd=str(HERE / "project"),
        capture_output=True, text=True,
    )
    check("merge_exit_code_zero", result.returncode == 0, result.stderr)

    if merged_path.exists():
        merged = json.loads(merged_path.read_text())
        hits = merged["files"][0]["hits"]
        check("merged_hits_are_exactly_the_union_of_both_runs", hits == {"0": 1, "1": 1, "2": 1}, str(hits))
        merged_path.unlink()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: merging two complementary "
        "runs (each covering a disjoint subset of the same file's lines) "
        "produces exactly the union -- no line either run touched is lost, and "
        "nothing neither run touched appears."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
