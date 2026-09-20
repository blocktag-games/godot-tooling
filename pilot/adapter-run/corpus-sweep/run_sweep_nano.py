#!/usr/bin/env python3
"""BP06: sweep the same pure-GDScript ("Group 1") tier-0/tier-1 corpus
against Nano Coverage (via its GdUnit4 session hook), the second real
candidate identified in BP05. Companion to run_sweep.py (gd-tools);
same 53 (fixture, input) pairs, same one-invocation-per-input rule.

Structural differences from the gd-tools sweep, both confirmed before
writing a single line of translation code:

  - Nano Coverage's LCOV output (coverage-report/lcov.info) is DIRECTLY
    keyed by real source line number (`DA:<line>,<count>`) -- there is
    no opaque file_id/line_id scheme to translate through, unlike
    gd-tools' plan.json. This sweep's `build_actual()` is correspondingly
    much smaller than run_sweep.py's.
  - Nano Coverage emits ZERO `BRDA` (branch) records anywhere in its
    addon source (confirmed by `grep -rn "BRDA" .../nano_coverage_godot/`
    returning nothing). It is a pure statement-coverage tool. Every
    branch-kind obligation in this corpus's oracles is therefore NOT
    APPLICABLE to Nano Coverage, not a missing_hits failure -- feeding
    them to compare() unfiltered would manufacture ~15 fake mismatches
    (one per branch-bearing fixture; see BRANCH_BEARING_FIXTURES) and
    bury the real, structural finding under noise. This script filters
    branch obligations out before comparing and records the excluded
    count per row instead.
  - GdUnit4's CLI (runtest.sh) has no single-test-name include filter
    (confirmed: `-i` is exclusion-only, `-a <suite>:<test>` is rejected
    with "does not exist"). Matches the working pattern already
    established in nano-coverage-gdunit4-f010_straight_line/: one test
    function per suite FILE, `-a test/<file>.gd` selects exactly that
    function. test/*.gd here holds 53 single-function suites generated
    from corpus-sweep/test_corpus.gd's GUT assertions, translated to
    GdUnitTestSuite's assert_that(...).is_equal(...) style.

Writes one row per (fixture, input) to a TSV report, plus an explicit
excluded_branch_obligations column so a reader never has to wonder
whether a clean row means "matched" or "had nothing left to compare
after filtering".
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/home/wade/code/godot-tooling")
SCRATCH = Path("/tmp/corpus-run/fixtures_nano")
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"

sys.path.insert(0, str(REPO_ROOT / "pilot/harness"))
from comparator import compare  # noqa: E402
from oracle import load_oracle, obligations_for_input  # noqa: E402

# Same 53 pairs as run_sweep.py's SWEEP list. The third element there
# (GUT function name) and here (GdUnit4 suite FILE name, no .gd) happen
# to be identical strings by construction (test_corpus_nano.gd's per-
# function split used the same names), so this list is generated from
# the same source rather than hand-duplicated -- see
# corpus-sweep/README.md's Nano Coverage section for how test/*.gd was
# produced.
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

# Under GdUnit4, is_equal() failures and the two deliberate runtime-
# error inputs are all real, expected non-passes -- unlike the GUT
# sweep, this script doesn't gate on suite pass/fail at all (see
# run_one()'s comment for why), so no EXPECTED_FAILURES set is needed
# here.

DA_RE = re.compile(r"^DA:(\d+),(\d+)$")
SF_RE = re.compile(r"^SF:(.+)$")


def run_one(suite_file: str) -> str:
    """Run one GdUnit4 suite file and return the raw lcov.info text.

    Unlike the gd-tools sweep, this does NOT gate on the suite's own
    pass/fail: GdUnit4's exit code and this repo's own is_equal()
    translation are a secondary concern to whether Nano Coverage
    produced a real lcov.info for the run, which is checked directly
    below by the caller.
    """
    reports_dir = SCRATCH / "coverage-report"
    if reports_dir.exists():
        shutil.rmtree(reports_dir)

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    subprocess.run(
        ["bash", "addons/gdUnit4/runtest.sh", "-a", f"test/{suite_file}.gd"],
        cwd=str(SCRATCH), env=env, capture_output=True, text=True, timeout=60,
    )
    lcov_path = reports_dir / "lcov.info"
    if not lcov_path.exists():
        raise RuntimeError(f"{suite_file}: no coverage-report/lcov.info produced")
    return lcov_path.read_text()


def parse_lcov(text: str, target_suffix: str) -> dict[str, int]:
    """Return {line_number_str: hit_count} for the SF: record whose path
    ends with target_suffix (e.g. "f010_straight_line/subject.gd") --
    lcov.info records are line-keyed directly, no id table involved."""
    hits: dict[str, int] = {}
    in_target = False
    for line in text.splitlines():
        sf_match = SF_RE.match(line)
        if sf_match:
            in_target = sf_match.group(1).endswith(target_suffix)
            continue
        if line == "end_of_record":
            in_target = False
            continue
        if in_target:
            da_match = DA_RE.match(line)
            if da_match:
                hits[da_match.group(1)] = int(da_match.group(2))
    return hits


def build_actual(lcov_text: str, source_rel_paths: list[str]) -> dict:
    """Build one comparator file entry per DISTINCT file the oracle's
    obligations reference (obligations_for_input's own .file attribute)
    -- NOT just the first one. A first version of this function only
    ever built a single-file `actual`, which silently mis-scored every
    multi-file fixture (F001: loaded.gd + unloaded.gd; F049: subject.gd
    + dependency.gd) as `missing_files` on the second file -- a bug in
    THIS script's translation, not a Nano Coverage finding. Caught by
    directly inspecting the raw lcov.info (it has a correct SF: record
    for both files in both cases) before trusting the aggregate diff.
    """
    import hashlib
    files = []
    for rel_path in source_rel_paths:
        hits = parse_lcov(lcov_text, rel_path)
        sha = hashlib.sha256((SCRATCH / rel_path).read_bytes()).hexdigest()
        files.append({"path": rel_path, "sha256": sha, "hits": hits, "branches": {}})
    return {"files": files}


def verify_controls() -> None:
    """Run BEFORE any sweep row is written or trusted -- same discipline
    as run_sweep.py's verify_controls(), adapted to what's actually
    known about Nano Coverage rather than copied from the gd-tools case.

    Positive control: F010 (no branch obligations at all) must compare
    clean using the exact same code path as the sweep loop.

    Filter-is-load-bearing control: F020/value_lte_0 has exactly one
    branch obligation (if_true, expected_hit=false). Comparing WITHOUT
    the branch filter must NOT be clean (Nano Coverage has no branch
    record for that line at all, so an unfiltered comparison scores it
    missing_hits) -- if it WERE clean unfiltered, either Nano Coverage
    unexpectedly does track branches now (a real finding to update the
    docstring over) or this script's obligation-splitting logic is a
    no-op and every "excluded_branch_obligations" count in the report
    would be fiction. Comparing WITH the filter must be clean.
    """
    oracle = load_oracle(REPO_ROOT / "pilot/fixtures/oracles/F010.json")
    obligations = obligations_for_input(oracle, "default")
    if any(o.evidence == "branches" for o in obligations):
        raise RuntimeError("F010 unexpectedly has branch obligations -- positive control assumption broken")
    lcov_text = run_one("test_F010_default")
    source_rel_paths = sorted({o.file for o in obligations})
    actual = build_actual(lcov_text, source_rel_paths)
    result = compare(obligations, actual, SCRATCH)
    if not result.is_clean:
        raise RuntimeError(
            f"POSITIVE CONTROL FAILED: F010/default must compare clean under "
            f"Nano Coverage but got false_hits={result.false_hits} "
            f"missing_hits={result.missing_hits}. The sweep script itself is "
            f"broken -- do not trust any row from this run."
        )
    print("CONTROL OK: F010/default compares clean under Nano Coverage (positive control)")

    oracle = load_oracle(REPO_ROOT / "pilot/fixtures/oracles/F020.json")
    all_obligations = obligations_for_input(oracle, "value_lte_0")
    branch_obligations = [o for o in all_obligations if o.evidence == "branches"]
    statement_obligations = [o for o in all_obligations if o.evidence != "branches"]
    # F020 has both if_true and if_false branch obligations per input
    # (see oracles/F020.json) -- the exact count isn't the point, only
    # that at least one exists to be excluded.
    if len(branch_obligations) == 0:
        raise RuntimeError("F020/value_lte_0 expected at least 1 branch obligation, found 0 -- control assumption broken")
    lcov_text = run_one("test_F020_value_lte_0")
    source_rel_paths = sorted({o.file for o in all_obligations})
    actual = build_actual(lcov_text, source_rel_paths)

    unfiltered_result = compare(all_obligations, actual, SCRATCH)
    if unfiltered_result.is_clean:
        raise RuntimeError(
            "FILTER CONTROL FAILED: F020/value_lte_0 compared clean WITHOUT "
            "excluding its one branch obligation -- either Nano Coverage now "
            "tracks branches (update the module docstring) or this is a stale "
            "control. Either way, the sweep's assumptions are wrong -- do not "
            "trust any excluded_branch_obligations count from this run."
        )
    filtered_result = compare(statement_obligations, actual, SCRATCH)
    if not filtered_result.is_clean:
        raise RuntimeError(
            f"FILTER CONTROL FAILED: F020/value_lte_0 should compare clean "
            f"once its one branch obligation is excluded, but got "
            f"false_hits={filtered_result.false_hits} missing_hits={filtered_result.missing_hits}. "
            f"The sweep script itself is broken -- do not trust any row from this run."
        )
    print("CONTROL OK: F020/value_lte_0's branch obligation is genuinely excluded, not a no-op (filter control)")


def main() -> int:
    verify_controls()
    rows = []
    for fixture_id, input_name, suite_file in SWEEP:
        oracle = load_oracle(REPO_ROOT / f"pilot/fixtures/oracles/{fixture_id}.json")
        all_obligations = obligations_for_input(oracle, input_name)
        # Nano Coverage has zero branch-tracking capability (see module
        # docstring) -- exclude branch obligations from the comparison
        # rather than let them register as false missing_hits, and
        # record exactly how many were excluded so a clean row can't be
        # misread as "this fixture has no branches to worry about".
        statement_obligations = [o for o in all_obligations if o.evidence != "branches"]
        excluded_count = len(all_obligations) - len(statement_obligations)

        try:
            lcov_text = run_one(suite_file)
        except Exception as e:
            rows.append((fixture_id, input_name, "ERROR", str(e), "", "", "", "", "0"))
            print(f"ERROR {fixture_id}/{input_name}: {e}")
            continue

        # Build one comparator file entry per DISTINCT file this
        # fixture's obligations reference -- most fixtures bind exactly
        # one (cases/<dir>/subject.gd), but F001 (loaded.gd + unloaded.gd)
        # and F049 (subject.gd + dependency.gd) bind two. An earlier
        # version of this loop only ever built the first file and
        # silently mis-scored the second one as missing_files -- caught
        # by inspecting the real lcov.info directly (it has a correct
        # SF: record for both files in both fixtures) before trusting
        # the aggregate diff.
        source_rel_paths = sorted({o.file for o in all_obligations})
        actual = build_actual(lcov_text, source_rel_paths)

        result = compare(statement_obligations, actual, SCRATCH)
        status = result.status
        rows.append((
            fixture_id, input_name, status,
            str(len(result.matched)), str(result.false_hits), str(result.missing_hits),
            str(result.missing_files), str(result.stale_files) + str(result.oracle_stale_files),
            str(excluded_count),
        ))
        marker = "OK" if result.is_clean else "MISMATCH"
        print(f"{marker} {fixture_id}/{input_name}: status={status} false_hits={result.false_hits} "
              f"missing_hits={result.missing_hits} excluded_branch_obligations={excluded_count}")

    out_path = Path("/tmp/corpus-run/results_nano.tsv")
    with out_path.open("w") as f:
        f.write("fixture\tinput\tstatus\tmatched_count\tfalse_hits\tmissing_hits\tmissing_files\tstale_files\texcluded_branch_obligations\n")
        for row in rows:
            f.write("\t".join(row) + "\n")
    print(f"\nWrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
