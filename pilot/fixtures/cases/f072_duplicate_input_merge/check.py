#!/usr/bin/env python3
"""BP06 ground-truth check for F072 against the real, pinned
gd-tools-cli 0.4.0.

Merges the SAME coverage-data file with itself (the simplest possible
duplicate-input case: identical bytes, not merely the same logical run
re-submitted with different bytes) and records gd-tools' actual policy.

Run: python3 check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
GD_TOOLS_VENV = HERE.parent.parent.parent / "gd-tools"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    gd_tools_bin = str(GD_TOOLS_VENV / ".venv/bin/gd-tools")
    merged_path = HERE / "merged.json"
    result = subprocess.run(
        [
            gd_tools_bin, "coverage", "merge",
            str(HERE / "run_a.json"),
            str(HERE / "run_a.json"),
            "--output", str(merged_path),
        ],
        cwd=str(HERE),
        capture_output=True, text=True,
    )
    check("merge_exit_code_zero", result.returncode == 0, result.stderr)
    output_text = (result.stdout + result.stderr).lower()
    check(
        "no_duplicate_input_warning_emitted",
        "identical" not in output_text and "already merged" not in output_text and "same file" not in output_text,
        f"stdout={result.stdout!r} stderr={result.stderr!r}",
    )

    if merged_path.exists():
        merged = json.loads(merged_path.read_text())
        hits = merged["files"][0]["hits"]
        original = json.loads((HERE / "run_a.json").read_text())["files"][0]["hits"]
        check(
            "duplicate_input_doubles_the_count_no_deduplication",
            hits.get("0") == 2 * original.get("0"),
            f"original={original} merged={hits} -- expected exact doubling if merge sums with no identity check",
        )
        merged_path.unlink()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0: merging identical input "
        "twice silently doubles the hit count, with no duplicate-input "
        "detection, warning, or deduplication of any kind."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
