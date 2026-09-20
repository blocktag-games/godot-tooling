# Nano Coverage + GdUnit4 integration vs. Godot 4.7.1

Resolves the open question from
[nano-coverage-godot-PIN.md](../../candidates/nano-coverage-godot-PIN.md)'s
finding 4: does GdUnit4's session hook perform whatever runtime
initialization the raw `ProjectBootstrapper`/`coverage_api_example.gd`
pattern skips?

## Reproduce

```sh
python3 check.py
```

(Requires Nano Coverage already built per `nano-coverage-godot-PIN.md`.)

## Result: yes -- the GdUnit4 integration works correctly

Enabling `nano_coverage/integrations/gdunit4` and running the editor-plugin
import step once (to register the session hook in project settings) is
enough. `addons/gdUnit4/runtest.sh` then runs cleanly: "Collected 4
execution hits", a real `coverage-report/lcov.info` is generated, exit code
0. Its content, for F010's unmodified `subject.gd`:

```
SF:subject/subject.gd
DA:4,1
DA:5,1
DA:6,1
LF:3
LH:3
```

This matches `oracles/F010.json` exactly (lines 4, 5, 6, each hit once).
`subject.gd`'s hash was also confirmed identical to the oracle's.

## What this means for BP05's finding 4

The crash in `nano-coverage-f010_straight_line/driver.gd` (calling
`ProjectBootstrapper.instrument_all_scripts()` directly, per the project's
own `coverage_api_example.gd`) is now narrowed: it is **not** a defect in
Nano Coverage's memory-instrumentation mode itself -- that mode works
correctly through its one shipped, real integration. The defect is
specifically in the documented example script's completeness (or in
whatever a bare headless script invocation is missing that GdUnit4's
session hook, or the editor-plugin-triggered import step that registers
it, provides). Still worth an upstream report -- the README explicitly
calls that example "the reference if you are building a CI/CD pipeline
script" -- but Nano Coverage itself is now a real, viable BP06 candidate
via GdUnit4, not a broken one.

## Still untested

Disk-instrumentation mode (the "no test framework needed" flagship
feature) -- still gated behind an editor UI toggle with no headless
equivalent identified.
