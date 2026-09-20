#!/usr/bin/env python3
"""BP06 ground-truth check for F003 against the real, pinned
gd-tools-cli 0.4.0.

The fixture is this directory itself: it contains project.godot and
deliberately zero .gd files, so gd-tools' own file discovery selects an
empty population. Confirms directly against the real tool that an
empty denominator produces 0% coverage, not 100%, a crash, or NaN.

Run: python3 check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).parent
GD_TOOLS_VENV = HERE.parent.parent.parent / "gd-tools"
sys.path.insert(0, str(GD_TOOLS_VENV / ".venv/lib/python3.13/site-packages"))

from gd_tools.coverage.plan_generator import generate_plan  # noqa: E402
from gd_tools.coverage.reporter import CoverageData, compute_summary  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    plan = generate_plan(str(HERE))
    check("population_is_genuinely_empty", len(plan.files) == 0, f"found {len(plan.files)} files")

    data = CoverageData(version=1, files=[])
    summary = compute_summary(plan, data)

    check("total_lines_is_zero", summary.total_lines == 0, str(summary.total_lines))
    check(
        "line_rate_is_zero_not_one",
        summary.line_rate == 0.0,
        f"expected 0.0, got {summary.line_rate} -- an empty denominator must not read as 100% coverage",
    )
    check("branch_rate_is_zero_not_one", summary.branch_rate == 0.0, str(summary.branch_rate))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: an empty source population "
        "reports 0.0 line_rate/branch_rate, not 100%, a crash, or NaN."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
