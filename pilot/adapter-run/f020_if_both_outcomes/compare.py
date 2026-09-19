#!/usr/bin/env python3
"""BP04: analyze the real gd-tools-cli 0.4.0 + GUT v9.7.1 covered run of
F020 (if with both outcomes) against its oracle
(pilot/fixtures/oracles/F020.json).

Unlike F010, F020's oracle expresses per-input conditional obligations
(a decision line's branch_outcomes, not a flat expected_hit bool), so
this does not reuse pilot/harness/comparator.py's Obligation format
directly -- it reports the raw plan/coverage evidence and states the
findings explicitly instead. Two runs are compared:

  .gd-tools/coverage/            -- both tests in one GUT invocation
                                     (test_true_branch + test_false_branch)
  true_only/.gd-tools/coverage/  -- only test_true_branch_only, a
                                     controlled follow-up run kept to
                                     resolve a branch-count ambiguity
                                     (see findings below; the run itself
                                     was not preserved as a full project
                                     to avoid duplicating the ~7MB
                                     vendored GUT/gd-tools addons twice
                                     more -- its plan/coverage JSON are
                                     copied into true_only/ instead)

Run: python3 compare.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent


def load(rel: str) -> dict:
    return json.loads((HERE / rel).read_text())


def summarize(label: str, plan: dict, coverage: dict) -> None:
    id_to_line = {e["id"]: (e["line"], e["type"], e.get("branch_type")) for e in plan["files"][0]["lines"]}
    hits = coverage["files"][0]["hits"]
    print(f"--- {label} ---")
    for id_str, count in sorted(hits.items(), key=lambda kv: int(kv[0])):
        line, kind, branch_type = id_to_line[int(id_str)]
        print(f"  line {line}: {kind}{f'({branch_type})' if branch_type else ''} hit {count}x")
    tracked_lines = {line for line, _, _ in id_to_line.values()}
    print(f"  lines tracked by plan: {sorted(tracked_lines)}")


def main() -> int:
    print("Oracle (F020.json) expects obligations on lines 4,5,6,8,9.")
    print("gd-tools' plan tracks only lines 5,6,7,8,9 -- line 4 (`var outcome: int`,")
    print("a bare declaration with no initializer) has NO trackable point at all in")
    print("gd-tools' plan. This is a real, confirmed finding: gd-tools' plan generator")
    print("does not create a statement obligation for an uninitialized var declaration,")
    print("unlike an initialized one (F010's `var doubled: int = x * 2` was tracked).")
    print("Line 4 is therefore MISSING from gd-tools' completeness accounting, not")
    print("falsely marked hit or unhit -- it simply never appears.")
    print()
    print("Branch attribution: gd-tools attributes the false-outcome branch obligation")
    print("to line 7 (the `else:` keyword line), not line 8 (the actual false-branch")
    print("body) that our oracle uses as its false-outcome anchor. Both are defensible")
    print("conventions but are NOT the same line -- a normalized comparison must remap")
    print("this explicitly, exactly as correctness-protocol.md warns: 'Do not interpret")
    print("an LCOV branch identifier as a shared cross-tool semantic identity without a")
    print("verified mapping.'")
    print()

    plan_both = load(".gd-tools/coverage/plan.json")
    cov_both = load(".gd-tools/coverage/coverage.json")
    summarize("both tests (test_true_branch + test_false_branch)", plan_both, cov_both)
    print()

    plan_true = load("true_only/plan.json")
    cov_true = load("true_only/coverage.json")
    summarize("true-branch test only (test_true_branch_only)", plan_true, cov_true)
    print()

    print("UNRESOLVED FINDING: in the true-branch-only run, the if_true branch (line 5)")
    print("hits exactly once, and if_false (line 7) is entirely absent from hits (0),")
    print("both exactly as expected for one call. But in the COMBINED two-test run,")
    print("if_true reports 2 hits, not the expected 1, while if_false correctly reports 1.")
    print("Each test function calls Subject.run() exactly once. Per")
    print("correctness-protocol.md's guidance to 'retain raw counts without asserting")
    print("count accuracy' when a count contract is unestablished: this is reported as")
    print("an open discrepancy, not a confirmed bug -- root cause (GUT test-ordering,")
    print("a double-dispatch during coverage instrumentation, or something specific to")
    print("running multiple test functions in one file) is uninvestigated and belongs")
    print("in BP05/BP06's fuller branch-semantics work, not this first adapter slice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
