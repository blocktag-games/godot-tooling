#!/usr/bin/env python3
"""BP04: analyze the real gd-tools-cli 0.4.0 + GUT v9.7.1 covered run of
F020 (if with both outcomes) against its oracle
(pilot/fixtures/oracles/F020.json).

F020's oracle now uses pilot/harness/oracle.py's unified schema
(obligations per named input, no decision/branch_outcomes lines
listed). This script does not yet load obligations through that schema
programmatically for the mechanical match/mismatch verdict -- it
reports the raw plan/coverage evidence and states the branch-tracking
finding explicitly, since that finding is about branch-counter
semantics gd-tools' plan doesn't represent as a statement obligation at
all. Three runs are compared, each a real, independent
`gd-tools test --coverage` invocation (not derived from one another):

  .gd-tools/coverage/  -- both tests in one GUT invocation
                          (test_true_branch + test_false_branch)
  true_only/           -- only test_true_branch_only (run(2), true path)
  false_only/          -- only test_false_branch_only (run(-2), false path)

true_only/ and false_only/ keep only the plan/coverage/lcov JSON, not a
full duplicate project, to avoid tripling the ~7MB vendored GUT/gd-tools
addons -- each is independently reproducible from subject.gd with a
single-test tests/test_subject.gd.

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
    hit_ids = {int(k) for k in hits}
    print(f"--- {label} ---")
    for eid, (line, kind, branch_type) in sorted(id_to_line.items(), key=lambda kv: kv[1][0]):
        count = hits.get(str(eid), 0)
        marker = f"hit {count}x" if eid in hit_ids else "NOT HIT (absent from coverage.json)"
        print(f"  line {line}: {kind}{f'({branch_type})' if branch_type else ''} {marker}")


def main() -> int:
    print("Oracle (F020.json) expects statement obligations on lines 4, 6, 8, 9")
    print("(per input; line 5 is the decision itself, not listed as a statement).")
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
    summarize("true-branch test only (run(2))", plan_true, cov_true)
    print()

    plan_false = load("false_only/plan.json")
    cov_false = load("false_only/coverage.json")
    summarize("false-branch test only (run(-2))", plan_false, cov_false)
    print()

    print("CONFIRMED FINDING: gd-tools' if_true and if_false branch trackers have")
    print("asymmetric placement semantics, verified directly from")
    print("addons/gd-tools-coverage/coverage.gd's _inject_trackers(): entries with")
    print("branch_type in {if_false, elif_true, match_case} are injected AFTER their")
    print("line, inside the branch body, so they only fire when that body actually")
    print("executes. if_true falls through to the function's `else` clause and is")
    print("injected BEFORE the `if` line itself -- so it fires on every evaluation of")
    print("the decision, regardless of which outcome is taken.")
    print()
    print("The false-branch-only run (run(-2) alone, never taking the true path) is the")
    print("proof: line 6 (the true-branch body, `outcome = 1`) is NOT HIT, correctly,")
    print("but gd-tools' own coverage.info still reports BRDA:5,0,0,1 and BRF:2 BRH:2 --")
    print("100% branch coverage, with the true branch's body never having executed.")
    print("gd-tools' branch-coverage percentage is therefore not a reliable signal that")
    print("both outcomes of an if/else were actually exercised: it can be satisfied by")
    print("merely reaching the decision, for the true-branch side specifically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
