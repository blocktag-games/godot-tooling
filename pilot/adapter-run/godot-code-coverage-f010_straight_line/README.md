# BP05: godot-code-coverage vs. Godot 4.7.1

Part of [BP05](../../../docs/benchmarks/implementation-plan.md). See
[../../candidates/godot-code-coverage/PIN.md](../../candidates/godot-code-coverage/PIN.md)
for the exact commit pinned and the full finding.

## Result: incompatible, silently

```sh
python3 check.py
```

`addons/coverage/coverage.gd`'s `NullCoverage` inner class overrides
`get_coverage_collector()` without matching the base class's declared return
type (`ScriptCoverageCollector`). Godot 4.7.1 rejects this at compile time:

```
SCRIPT ERROR: Parse Error: Cannot return value of type "NullCoverage" because
the function return type is "ScriptCoverageCollector".
```

This breaks `coverage.gd` entirely, which breaks the pre/post-run hooks that
depend on it. But GUT does not halt the overall test run when a hook fails to
compile -- it logs the script errors, runs the tests anyway, and reports
**"All tests passed!" with exit code 0.** No `coverage_output.json` is ever
written. A CI pipeline checking only the test-run exit code would never learn
that coverage was silently absent for the entire run.

This resolves the open question the original tooling survey flagged
("Godot 4.7 is unverified" -- `docs/research/2026-09-06-godot-tooling-survey.md`):
as of the pinned commit (`3c92852d`, the actual latest upstream commit,
confirmed 2026-09-19), it is **not compatible**.

## What this does and doesn't establish

- Confirms real incompatibility with the specific pinned Godot 4.7.1 build,
  reproducibly, via `check.py`.
- Does not attempt to patch `coverage.gd` and retest -- the fix (making
  `NullCoverage.get_coverage_collector()`'s return type match its base class)
  looks small, but this evaluation is of the tool as shipped, not a
  hypothetical fork. Worth reporting upstream, matching this project's
  existing practice (`docs/upstream/gut-bugs.md`).
- Does not test godot-code-coverage's manual/standalone mode
  (`addons/coverage/coverage_tree.gd`, driven via `--scene=`) or its merge
  tool (`addons/coverage/merge_coverage.gd`) -- both also depend on the same
  broken `coverage.gd`, so they would fail identically; not separately
  verified here.
