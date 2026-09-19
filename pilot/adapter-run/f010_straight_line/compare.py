#!/usr/bin/env python3
"""BP04: compare the real gd-tools-cli 0.4.0 + GUT v9.7.1 covered run of
F010 against its independently-authored oracle (pilot/fixtures/oracles/
F010.json), using the BP03 harness's comparator.

gd-tools' raw coverage.json keys hits by an internal per-file trackable
point *id* (0-indexed, assigned by its plan generator), not by source
line number. plan.json maps id -> line. This script does that
translation explicitly before handing normalized {line: count} hits to
the comparator, rather than trusting gd-tools' own line-numbered LCOV
output (which is a *derived* report, not the primary evidence).

Run: python3 compare.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "pilot" / "harness"))
from comparator import Obligation, compare  # noqa: E402


def main() -> int:
    oracle = json.loads((REPO_ROOT / "pilot/fixtures/oracles/F010.json").read_text())
    plan = json.loads((HERE / ".gd-tools/coverage/plan.json").read_text())
    coverage = json.loads((HERE / ".gd-tools/coverage/coverage.json").read_text())

    plan_file = plan["files"][0]
    assert plan_file["path"] == "res://subject/subject.gd"
    plan_sha = plan_file["source_hash"].removeprefix("sha256:")

    id_to_line = {entry["id"]: entry["line"] for entry in plan_file["lines"]}
    cov_file = coverage["files"][0]
    hits_by_line = {
        str(id_to_line[int(id_str)]): count for id_str, count in cov_file["hits"].items()
    }

    actual = {"files": [{"path": "subject/subject.gd", "sha256": plan_sha, "hits": hits_by_line}]}

    oracle_obligations = oracle["files"][0]["obligations"]
    oracle_sha = oracle["files"][0]["sha256"]
    print(f"oracle sha256:      {oracle_sha}")
    print(f"plan.json sha256:   {plan_sha}")
    print(f"source_hash_match:  {oracle_sha == plan_sha}")

    obligations = [
        Obligation(file="subject/subject.gd", sha256=oracle_sha, line=o["line"], expected_hit=o["expected_hit"])
        for o in oracle_obligations
    ]

    result = compare(obligations, actual, HERE)
    print()
    print(f"status:        {result.status}")
    print(f"matched:       {result.matched}")
    print(f"false_hits:    {result.false_hits}")
    print(f"missing_hits:  {result.missing_hits}")
    print(f"missing_files: {result.missing_files}")
    print(f"stale_files:   {result.stale_files}")

    return 0 if result.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
