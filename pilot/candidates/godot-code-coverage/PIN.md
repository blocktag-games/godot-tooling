# godot-code-coverage pin

- Upstream: https://github.com/jamie-pate/godot-code-coverage
- Commit: `3c92852d0822a1a8ed3d7d0a89b489c636afe992` (2025-12-17T16:34:56-08:00, "Make coverage thread collection safe")
- Confirmed via GitHub API on 2026-09-19 that this is upstream's latest commit -- no newer fix exists.
- License: MIT (see `LICENSE`)
- Only `addons/coverage/` is vendored here (the reusable instrumentation library: `coverage.gd`, `coverage_tree.gd`, `merge_coverage.gd`). The upstream repo's own example project, tests, and vendored GUT submodule are not needed and not vendored -- this project uses its own pinned GUT v9.7.1 instead (see `docs/benchmarks/pilot-environment.md`).

## BP05 finding: incompatible with Godot 4.7.1

`addons/coverage/coverage.gd`'s `NullCoverage` inner class (line 462) overrides
`get_coverage_collector(_script_name) -> ...` without matching the base
`Coverage` class's declared return type `ScriptCoverageCollector` (line 493).
Godot 4.7.1 rejects this at script-compile time:

```
SCRIPT ERROR: Parse Error: Cannot return value of type "NullCoverage" because
the function return type is "ScriptCoverageCollector".
    at: GDScript::reload (res://addons/coverage/coverage.gd:463)
```

This is a real, reproducible, current break -- not a hypothetical or a stale
README claim. See `pilot/adapter-run/godot-code-coverage-f010_straight_line/`
for the full reproduction. Its practical severity: the failure is **silent**
from a CI perspective. GUT continues running tests despite the pre-run hook
failing to compile, reports "All tests passed!", and exits 0 -- no
`coverage_output.json` is ever written, and nothing in the test run's own
exit code or summary indicates coverage never activated.

This is a candidate for an upstream bug report, matching this project's
existing practice for GUT (`docs/upstream/gut-bugs.md`) of preferring
upstream contribution over silently working around a defect.
