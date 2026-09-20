"""Oracle schema and loader for pilot/fixtures/oracles/*.json.

Schema (line-hit oracles -- most tier-0 cases):
{
  "id", "tier", "domain", "case", "requirement": str,
  "files": [{"path": <relative to pilot/fixtures/>, "sha256": str,
             "role"?: str, "note"?: str}],
  "inputs": [
    {
      "name": str, "call": str, "expected_result"?: any,
      "obligations": [
        {"file": <matches a files[].path>, "line": int, "kind": str,
         "expected_hit": bool, "expected_count"?: int, "note"?: str}
      ]
    }, ...
  ],
  ... evidence/commentary fields (measured_on_engine, notes, author,
      reviewer, ambiguities, etc.) are free-form and not consumed here.
}

A line NOT listed in any input's obligations is not a trackable
obligation at all under this project's line convention (e.g. a
continuation line of a multi-line statement, or a non-executable
declaration) -- absence IS the answer, replacing the old ad hoc
"not_a_separate_obligation" sentinel and "branch_outcomes" object
shapes that predated this loader. A line listed with expected_hit:
false for one input and expected_hit: true for another is the SAME
obligation, whose hit state legitimately varies by input -- exactly
what a branch requires.

Decision/branch lines (an `if`, `elif`, `for`/`while` header, or `match`
arm) ARE first-class obligations, listed exactly like a statement line:
{"file": ..., "line": <the decision's own line>, "kind": "branch",
"branch_type": "if_true" | "if_false" | "elif_true" | "loop_header" |
"match_case", "expected_hit": bool}. `kind` and `branch_type` are
documentation for a human reader (and for a future
branch-vs-statement-aware comparator); comparator.compare() does not
currently distinguish them from a statement obligation -- both are
just a (file, line, expected_hit) fact to it. This was a real gap
identified on 2026-09-19 (F020's original oracle omitted lines 5 and 7,
the decision lines themselves, treating them as "keyword lines, not
body-line obligations" -- which meant F020's real gd-tools comparison
needed hand-written prose instead of a mechanical compare() call).
Omitting decision lines is no longer this project's convention;
tier-1's control-flow cases (F022 onward) include them.

File paths in "files[].path" and "obligations[].file" are always
relative to pilot/fixtures/ (i.e. include the "cases/<case>/" prefix),
regardless of where a specific run's project root actually is. A
caller comparing against a real run rooted elsewhere (e.g. BP04's
adapter-run projects) is responsible for translating paths to match
that run's layout, the same way pilot/adapter-run/f010_straight_line/
compare.py already does.

Not every oracle fits the line-hit shape: F062, F064, F065, and F071
test process/artifact behavior (exit codes, file existence, merge
output) rather than per-line hits, and have no top-level
"inputs[].obligations" at all. obligations_for_input() raises KeyError
for those, by design -- that is not a schema gap, it is those oracles
correctly not claiming a kind of evidence they don't have.
"""
from __future__ import annotations

import json
from pathlib import Path

from comparator import Obligation


def load_oracle(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha_for_file(oracle: dict, file_path: str) -> str:
    for f in oracle["files"]:
        if f["path"] == file_path:
            return f["sha256"]
    raise KeyError(f"file {file_path!r} not declared in oracle {oracle.get('id')}'s files[]")


def obligations_for_input(oracle: dict, input_name: str) -> list[Obligation]:
    """Build the Obligation list comparator.compare() expects, for one
    named input. Raises KeyError if the input doesn't exist, or if this
    oracle has no line-hit obligations at all (see module docstring).
    """
    for inp in oracle["inputs"]:
        if inp["name"] == input_name:
            if "obligations" not in inp:
                raise KeyError(
                    f"oracle {oracle.get('id')} input {input_name!r} has no obligations "
                    "(this oracle tests process/artifact behavior, not line hits)"
                )
            return [
                Obligation(
                    file=o["file"],
                    sha256=_sha_for_file(oracle, o["file"]),
                    line=o["line"],
                    expected_hit=bool(o["expected_hit"]),
                )
                for o in inp["obligations"]
            ]
    raise KeyError(f"no input named {input_name!r} in oracle {oracle.get('id')}")


def union_obligations(oracle: dict) -> list[Obligation]:
    """Union across all of an oracle's inputs: an obligation is
    expected_hit=True if ANY input hits it. Models comparing against a
    cumulative report -- e.g. one GUT suite run covering several named
    inputs in a single invocation, the shape BP04's F020 runs actually
    produced.
    """
    merged: dict[tuple[str, int], Obligation] = {}
    for inp in oracle["inputs"]:
        for o in inp.get("obligations", []):
            key = (o["file"], o["line"])
            sha = _sha_for_file(oracle, o["file"])
            if key not in merged:
                merged[key] = Obligation(
                    file=o["file"], sha256=sha, line=o["line"], expected_hit=bool(o["expected_hit"])
                )
            elif o["expected_hit"]:
                merged[key].expected_hit = True
    return list(merged.values())
