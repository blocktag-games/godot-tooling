#!/usr/bin/env python3
"""BP02/BP04 ground-truth check for F071 against the real, pinned
gd-tools-cli 0.4.0.

project_v1 and project_v2 model the same logical project at two points
in time: alpha.gd is deleted and aardvark.gd is added between them.
Godot's file discovery order gives each project's files different
file_id assignments, so file_id 0 means alpha.gd in one plan and beta.gd
in the other -- and gd-tools' raw coverage-data JSON format carries no
path or source hash at all (confirmed directly from
gd_tools.coverage.reporter.read_coverage_json's own docstring: "A
`path` field is NOT required in the coverage data -- path resolution
happens at report-generation time via the plan").

This script regenerates both plans, confirms the file_id collision is
real, then runs the actual `gd-tools coverage merge` CLI against two
hand-crafted coverage-data files and verifies it blends unrelated
files' hit counts under a shared file_id with no warning.

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
    plan_v1 = generate_plan(str(HERE / "project_v1"))
    plan_v2 = generate_plan(str(HERE / "project_v2"))
    v1_by_id = {fp.file_id: fp.path for fp in plan_v1.files}
    v2_by_id = {fp.file_id: fp.path for fp in plan_v2.files}
    print(f"plan_v1 file_ids: {v1_by_id}")
    print(f"plan_v2 file_ids: {v2_by_id}")

    check(
        "file_id_0_means_different_files_in_each_plan",
        v1_by_id.get(0) != v2_by_id.get(0),
        f"v1[0]={v1_by_id.get(0)!r} v2[0]={v2_by_id.get(0)!r}",
    )

    merged_path = HERE / "merged.json"
    gd_tools_bin = str(GD_TOOLS_VENV / ".venv/bin/gd-tools")
    result = subprocess.run(
        [
            gd_tools_bin, "coverage", "merge",
            str(HERE / "session_v1_coverage.json"),
            str(HERE / "session_v2_coverage.json"),
            "--output", str(merged_path),
        ],
        cwd=str(HERE / "project_v1"),
        capture_output=True,
        text=True,
    )
    check("merge_exit_code_zero", result.returncode == 0, result.stderr)
    check(
        "merge_emits_no_source_mismatch_warning",
        "hash" not in result.stdout.lower() and "hash" not in result.stderr.lower()
        and "mismatch" not in result.stdout.lower() and "mismatch" not in result.stderr.lower(),
        f"stdout={result.stdout!r} stderr={result.stderr!r}",
    )

    if merged_path.exists():
        merged = json.loads(merged_path.read_text())
        by_id = {f["file_id"]: f["hits"] for f in merged["files"]}
        check(
            "file_id_0_hits_blended_from_two_unrelated_files",
            by_id.get(0, {}).get("4") == 12,
            f"expected blended count 5+7=12 for file_id 0, got {by_id.get(0)}",
        )
        check(
            "file_id_1_hits_blended_from_two_unrelated_files",
            by_id.get(1, {}).get("4") == 5,
            f"expected blended count 3+2=5 for file_id 1, got {by_id.get(1)}",
        )
        merged_path.unlink()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "F071 confirmed against real gd-tools-cli 0.4.0: coverage merge blends "
        "hit counts from two unrelated files sharing a file_id, with no warning."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
