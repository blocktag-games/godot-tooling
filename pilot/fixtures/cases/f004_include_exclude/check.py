#!/usr/bin/env python3
"""BP06 ground-truth check for F004 against the real, pinned
gd-tools-cli 0.4.0: app.gd should be selected, addons/vendor_lib/vendor.gd
and tests/test_something.gd should be excluded by gd-tools' default
exclude/test-dir rules.

Run: python3 check.py
"""
from __future__ import annotations

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
    plan = generate_plan(str(HERE))
    paths = {fp.path for fp in plan.files}
    print(f"plan files: {sorted(paths)}")

    check("app_gd_included", "res://app.gd" in paths, str(paths))
    check("vendor_gd_excluded", "res://addons/vendor_lib/vendor.gd" not in paths, str(paths))
    check("test_gd_excluded", "res://tests/test_something.gd" not in paths, str(paths))
    check("exactly_one_file_selected", len(paths) == 1, f"expected exactly app.gd, got {paths}")

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: default exclude rules correctly "
        "distinguish application source from vendor addons and test files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
