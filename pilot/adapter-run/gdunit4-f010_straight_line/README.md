# BP05: GdUnit4 parity driver

Part of [BP05](../../../docs/benchmarks/implementation-plan.md)'s "add a
GdUnit4 driver" item. See
[../../candidates/gdUnit4/PIN.md](../../candidates/gdUnit4/PIN.md) for the
exact pinned release and license.

## Reproduce

```sh
python3 check.py
```

Restores the vendored `addons/gdUnit4/` (from
`pilot/candidates/gdUnit4/addons/gdUnit4/`), clears prior state, and runs
GdUnit4's own `runtest.sh` against `test/test_subject.gd` -- a real GdUnit4
test (`assert_int(...).is_equal(...)`) exercising F010's unmodified
`subject.gd`.

## Result

Clean: 1/1 test cases pass, exit code 0, on the pinned Godot 4.7.1 binary.
No coverage tool is involved here -- this closes BP05's driver requirement
(a working, real GdUnit4 invocation to pair against candidates that support
it), not a coverage correctness case.
