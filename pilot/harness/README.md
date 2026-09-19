# BP03 harness

Part of [BP03](../../docs/benchmarks/implementation-plan.md): minimal
orchestration and evidence records. Stdlib-only Python (no dependencies to
install) — run directly with `python3`, not through the `pilot/gd-tools`
Pipenv environment.

## Modules

| File | Purpose |
| --- | --- |
| `comparator.py` | Compares a normalized actual coverage report against an oracle's obligations. Distinguishes match / false hit / missing hit / missing file / stale source, and raises `MalformedReportError` rather than treating an unparseable report as empty or successful. |
| `runner.py` | Runs an adapter/subject process with an enforced timeout, or terminates it as soon as a known stdout marker appears (for testing graceful interruption). |
| `faults.py` | Fault-injection helpers (make a file/dir unwritable, truncate a file) for harness-dependent fixtures. |
| `self_test.py` | BP03's completion evidence. |

## Completion evidence

```sh
python3 self_test.py
```

Exercises the comparator with hand-crafted synthetic reports, per
correctness-protocol.md's instruction to "prove a false hit, missing file,
stale report, or truncated report cannot silently become a successful
complete measurement in our own harness using synthetic adapter inputs":

- **Synthetic failure controls** (must all be caught): false hit, missing
  hit, missing file, stale source hash, malformed report shape, truncated
  JSON.
- **Positive controls** (must both pass cleanly): a hand-written correct
  report scores a full match; a no-op adapter's identical baseline/covered
  output is recognized as no behavioral difference. Without these, a
  harness that simply rejects everything would pass the failure controls
  above for the wrong reason.

All 8 checks pass on this comparator implementation.

## Status

This is the harness's own self-test suite, not yet wired to a real
adapter invocation. Group 3 fixtures (F008, F062, F064, F065, F071) use
these modules against real processes (GUT, gd-tools) and hand-crafted
inputs; BP04 wires the harness to the actual gd-tools+GUT run.
