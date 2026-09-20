#!/usr/bin/env python3
"""BP06: sweep the pure-GDScript ("Group 1") tier-0/tier-1 corpus
against real gd-tools-cli 0.4.0, one gd-tools invocation per oracle
input (never batched -- a shared process's coverage report is
cumulative and would falsely satisfy an input's "not yet reached"
obligations with a LATER input's hits in the same run).

For each oracle input, this script:
  1. Runs `gd-tools test --coverage --test <func>` against the scratch
     copy of pilot/fixtures/ (already has GUT + gd-tools-coverage
     installed, project.godot configured).
  2. Reads plan.json (ALL trackable files, even ones with zero hits)
     and coverage.json (only files gd-tools' tracker actually called
     hit() for at least once -- a file present in the plan but ABSENT
     from coverage.json has zero hits, it is not "untracked"; treating
     a plan-present/coverage-absent file as `missing_files` would be a
     translation bug, not a real finding, so this script explicitly
     defaults every plan file to hits={} before overlaying whatever
     coverage.json actually recorded).
  3. Translates plan entries into the comparator's "hits" (by line) and
     "branches" (keyed "<line>:<branch_type>") dicts. A branch-type
     entry with no paired counter for the opposite outcome (if_true,
     elif_true, loop_body) populates BOTH: gd-tools has no separate
     "reached" counter for these lines distinct from the (mislabeled)
     branch counter, so the same raw count IS both facts. Also applies
     BRANCH_TYPE_ALIASES ("loop_body" -> "loop_entered") since this
     corpus's oracle convention and gd-tools' own internal vocabulary
     independently chose different labels for the same concept -- a
     naming mismatch to translate, not a behavioral finding.
  4. Loads the fixture's oracle, retargets its obligations from
     pilot/fixtures/-relative paths (already correct here, no
     retargeting needed since this scratch project IS a copy of
     pilot/fixtures/), and calls pilot/harness/comparator.compare().

Writes one row per (fixture, input) to a TSV report.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/home/wade/code/godot-tooling")
SCRATCH = Path("/tmp/corpus-run/fixtures")
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"

sys.path.insert(0, str(REPO_ROOT / "pilot/harness"))
from comparator import compare  # noqa: E402
from oracle import load_oracle, obligations_for_input  # noqa: E402

# (fixture_id, input_name, gut_test_func_name)
SWEEP: list[tuple[str, str, str]] = [
    ("F001", "default", "test_F001_default"),
    ("F002", "default", "test_F002_default"),
    ("F010", "default", "test_F010_default"),
    ("F012", "default", "test_F012_default"),
    ("F020", "value_gt_0", "test_F020_value_gt_0"),
    ("F020", "value_lte_0", "test_F020_value_lte_0"),
    ("F021", "value_gt_0", "test_F021_value_gt_0"),
    ("F021", "value_lte_0", "test_F021_value_lte_0"),
    ("F022", "big", "test_F022_big"),
    ("F022", "small", "test_F022_small"),
    ("F022", "zero", "test_F022_zero"),
    ("F022", "none", "test_F022_none"),
    ("F023", "both", "test_F023_both"),
    ("F023", "only_a", "test_F023_only_a"),
    ("F023", "neither", "test_F023_neither"),
    ("F024", "zero", "test_F024_zero"),
    ("F024", "one", "test_F024_one"),
    ("F024", "many", "test_F024_many"),
    ("F025", "zero", "test_F025_zero"),
    ("F025", "one", "test_F025_one"),
    ("F025", "many", "test_F025_many"),
    ("F026", "continue_only", "test_F026_continue_only"),
    ("F026", "break_only", "test_F026_break_only"),
    ("F026", "neither", "test_F026_neither"),
    ("F026", "empty", "test_F026_empty"),
    ("F027", "one", "test_F027_one"),
    ("F027", "two", "test_F027_two"),
    ("F027", "other", "test_F027_other"),
    ("F029", "positive", "test_F029_positive"),
    ("F029", "non_positive", "test_F029_non_positive"),
    ("F030", "and_evaluated", "test_F030_and_evaluated"),
    ("F030", "and_short_circuited", "test_F030_and_short_circuited"),
    ("F030", "or_evaluated", "test_F030_or_evaluated"),
    ("F030", "or_short_circuited", "test_F030_or_short_circuited"),
    ("F011", "default", "test_F011_default"),
    ("F013", "all_complete", "test_F013_all_complete"),
    ("F013", "middle_statement_errors", "test_F013_middle_statement_errors"),
    ("F014", "early_return_taken", "test_F014_early_return_taken"),
    ("F014", "falls_through", "test_F014_falls_through"),
    ("F015", "completes_normally", "test_F015_completes_normally"),
    ("F015", "reached_but_not_completed", "test_F015_reached_but_not_completed"),
    ("F016", "three_identical_calls", "test_F016_three_identical_calls"),
    ("F032", "default", "test_F032_default"),
    ("F033", "invoked", "test_F033_invoked"),
    ("F033", "made_but_not_invoked", "test_F033_made_but_not_invoked"),
    ("F034", "derived_dispatch", "test_F034_derived_dispatch"),
    ("F034", "base_dispatch", "test_F034_base_dispatch"),
    ("F035", "default", "test_F035_default"),
    ("F036", "default", "test_F036_default"),
    ("F037", "omitted_argument", "test_F037_omitted_argument"),
    ("F037", "supplied_argument", "test_F037_supplied_argument"),
    ("F049", "uses_preloaded", "test_F049_uses_preloaded"),
    ("F049", "uses_loaded", "test_F049_uses_loaded"),
]


def run_one(test_func: str) -> tuple[dict, dict]:
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run(
        [str(GD_TOOLS_BIN), "test", "--coverage", "--test", test_func],
        cwd=str(SCRATCH), env=env, capture_output=True, text=True, timeout=60,
    )
    # GUT 9.7.1 scores any engine error raised during a test as a failure,
    # so the two deliberate runtime-error inputs fail under GUT by design;
    # their coverage data is still valid (F063: outcome and coverage are
    # independent). Every other input must pass.
    passed = "All 1 test(s) passed" in result.stdout
    if passed == (test_func in EXPECTED_GUT_FAILURES):
        raise RuntimeError(f"unexpected GUT outcome for {test_func} (passed={passed}):\n{result.stdout}\n{result.stderr}")
    plan = json.loads((SCRATCH / ".gd-tools/coverage/plan.json").read_text())
    coverage_path = SCRATCH / ".gd-tools/coverage/coverage.json"
    coverage = json.loads(coverage_path.read_text()) if coverage_path.exists() else {"files": []}
    return plan, coverage


# gd-tools' own internal branch_type vocabulary doesn't always match
# this corpus's oracle labels for the same construct -- both are
# independently-chosen free-text labels, not a shared standard. Only
# one collision exists in this corpus: gd-tools calls a while/for loop
# header's branch point "loop_body"; every oracle in this corpus calls
# the same concept "loop_entered". This is a naming mismatch to
# translate, not a behavioral deviation to report.
BRANCH_TYPE_ALIASES = {"loop_body": "loop_entered"}

EXPECTED_GUT_FAILURES = {
    "test_F013_middle_statement_errors",
    "test_F015_reached_but_not_completed",
}


def build_actual(plan: dict, coverage: dict) -> dict:
    """Translate gd-tools' raw plan+coverage into the comparator's
    {"files": [{"path", "sha256", "hits", "branches"}]} shape, defaulting
    every plan-tracked file to zero hits before overlaying what
    coverage.json actually recorded (see module docstring point 2)."""
    cov_by_id = {f["file_id"]: f["hits"] for f in coverage.get("files", [])}
    actual_files = []
    for pf in plan["files"]:
        id_to_line = {e["id"]: e["line"] for e in pf["lines"]}
        id_to_type = {e["id"]: (e.get("type"), e.get("branch_type")) for e in pf["lines"]}
        raw_hits = cov_by_id.get(pf["file_id"], {})
        hits: dict[str, int] = {}
        branches: dict[str, int] = {}
        for id_str, count in raw_hits.items():
            entry_id = int(id_str)
            line = id_to_line[entry_id]
            kind, branch_type = id_to_type[entry_id]
            # A branch-type entry (if_true/elif_true with no paired
            # if_false/elif_false counter) is gd-tools' ONLY trackable
            # point for that line -- there is no separate "reached"
            # counter distinct from the (mislabeled) branch counter.
            # Populate both: the statement-reached fact IS genuinely
            # true whenever this fires at all, regardless of outcome;
            # this is what makes the corpus mechanically detect gd-tools'
            # if_true/elif_true counter firing on every evaluation
            # (BP04's finding) as a false_hit on the BRANCH obligation
            # specifically, not a false missing_hits on the STATEMENT
            # obligation for the same line.
            hits[str(line)] = count
            if kind == "branch":
                branch_type = BRANCH_TYPE_ALIASES.get(branch_type, branch_type)
                branches[f"{line}:{branch_type}"] = count
        actual_files.append({
            "path": pf["path"].removeprefix("res://"),
            "sha256": pf["source_hash"].removeprefix("sha256:"),
            "hits": hits,
            "branches": branches,
        })
    return {"files": actual_files}


def main() -> int:
    rows = []
    for fixture_id, input_name, test_func in SWEEP:
        oracle = load_oracle(REPO_ROOT / f"pilot/fixtures/oracles/{fixture_id}.json")
        obligations = obligations_for_input(oracle, input_name)
        try:
            plan, coverage = run_one(test_func)
        except Exception as e:
            rows.append((fixture_id, input_name, "ERROR", str(e), "", "", "", ""))
            print(f"ERROR {fixture_id}/{input_name}: {e}")
            continue
        actual = build_actual(plan, coverage)
        result = compare(obligations, actual, SCRATCH)
        status = result.status
        rows.append((
            fixture_id, input_name, status,
            str(len(result.matched)), str(result.false_hits), str(result.missing_hits),
            str(result.missing_files), str(result.stale_files) + str(result.oracle_stale_files),
        ))
        marker = "OK" if result.is_clean else "MISMATCH"
        print(f"{marker} {fixture_id}/{input_name}: status={status} false_hits={result.false_hits} missing_hits={result.missing_hits}")

    out_path = Path("/tmp/corpus-run/results.tsv")
    with out_path.open("w") as f:
        f.write("fixture\tinput\tstatus\tmatched_count\tfalse_hits\tmissing_hits\tmissing_files\tstale_files\n")
        for row in rows:
            f.write("\t".join(row) + "\n")
    print(f"\nWrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
