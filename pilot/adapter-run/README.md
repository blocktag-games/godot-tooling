# BP04: first coverage adapter run

Part of [BP04](../../docs/benchmarks/implementation-plan.md): the real gd-tools-cli
0.4.0 + GUT v9.7.1 adapter, run against the pinned Godot 4.7.1 binary, exercising
tier-0 fixtures from [pilot/fixtures/](../fixtures/). This is where the tool-source
predictions from BP01/BP02 either get confirmed or corrected by an actual run.

## Setup

Each case is a minimal Godot project scaffolded with `gd-tools init --non-interactive`
(`GODOT_BIN` pointed at the pinned binary), then:
- `addons/gut/` replaced with the BP01-pinned v9.7.1 (gd-tools bundles v9.7.0 by
  default -- itself a minor finding: gd-tools' own vendored GUT is one release
  behind the version this study pinned).
- `gd-tools.toml`'s `[coverage]` section: `enabled = true`, `format = "lcov"`.
- One GUT test file per fixture, calling the fixture's existing `subject.gd`
  unmodified (no fixture was rewritten to suit gd-tools' integration style).
- Run: `gd-tools test --coverage`.

Vendored addons and `.godot/` import caches are gitignored (see repo
`.gitignore`) to avoid duplicating the ~7MB GUT addon per case -- it's already
committed once in full under `pilot/fixtures/cases/f064_zero_requested_tests/addons/`.
The measured evidence itself (`.gd-tools/coverage/{plan,coverage}.json`,
`coverage.info`, `results.xml`) is small and is committed directly.

## F010 (straight-line body) -- clean match

```sh
cd f010_straight_line && python3 compare.py
```

Result: **`status: match`**, all three obligations (lines 4, 5, 6) matched exactly
against `oracles/F010.json`, using `pilot/harness/comparator.py` for the
line-by-line comparison. `plan.json`'s recorded source hash matches the oracle's
hash byte-for-byte. The test itself (`assert_eq(Subject.run(3), 7)`) passed,
confirming instrumentation didn't change behavior.

This is deliberately unglamorous: the first real end-to-end run should be
boring when the tool is behaving. It establishes that the baseline-to-report
pipeline itself works before layering in the more contested cases.

## F020 (if with both outcomes) -- two real findings, one open question

```sh
cd f020_if_both_outcomes && python3 compare.py
```

Result: **not a clean match against the oracle**, for a specific, identified reason:

1. **`var outcome: int` (line 4, no initializer) has no trackable point in
   gd-tools' plan at all.** It's not marked unhit -- it's simply absent from the
   plan's `lines` list, unlike F010's initialized `var doubled: int = x * 2`,
   which was tracked. A real completeness gap: a bare declaration silently
   doesn't count toward the denominator.
2. **Branch line attribution differs from the oracle's convention.** gd-tools
   anchors the false-outcome branch to line 7 (`else:`), not line 8 (the actual
   false-branch body) that the oracle uses. Neither is wrong on its own, but they
   are not the same line, and comparing them naively would produce a false
   mismatch -- exactly the cross-tool branch-identity risk
   `correctness-protocol.md` warns about.
3. **Open, unresolved branch-count anomaly.** Running only `test_true_branch_only`
   (one call, true outcome) gives the correct count: if_true hit 1x, if_false
   absent (0x). Running both `test_true_branch` and `test_false_branch` in one
   GUT invocation gives if_true hit **2x**, not the expected 1x, while if_false
   still correctly shows 1x. Each test calls `Subject.run()` exactly once. Root
   cause is not identified -- this is reported as an open discrepancy per
   `correctness-protocol.md`'s instruction to retain raw counts rather than
   assert count accuracy when a count contract isn't established, not asserted
   as a confirmed defect.

## What this does and doesn't establish

- Confirms F008's and F071's source-reading-based predictions transfer to a real
  end-to-end `gd-tools test --coverage` invocation (not just direct calls into
  gd-tools' Python API, which is what F008/F071's fixtures used).
- Line coverage on a no-branch case (F010) is accurate.
- Branch coverage exists (contradicting nothing from the earlier survey, which
  only flagged branch coverage as *unverified*, not absent) but has at least one
  completeness gap (uninitialized declarations) and one open count anomaly that
  need dedicated investigation before trusting branch percentages at face value.
- Does **not** re-run F040/F091/F045/F060's real-adapter equivalents (autoload
  timing, await, reload-with-real-instrumentation) -- those remain source-read
  predictions pending their own BP04/BP05-style real runs.
- Does **not** constitute the full tier-0 or tier-1 corpus run -- per
  `implementation-plan.md`, "the first usable contribution is BP04, not
  completion of every catalog case."
