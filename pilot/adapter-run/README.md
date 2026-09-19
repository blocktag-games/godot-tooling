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

## F020 (if with both outcomes) -- three real findings

```sh
cd f020_if_both_outcomes && python3 compare.py
```

Result: **not a clean match against the oracle**, for three specific, confirmed reasons:

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
3. **gd-tools' `if_true` and `if_false` branch counters have asymmetric,
   incompatible semantics -- confirmed by three independent runs (both tests
   together, true-only, false-only; see `false_only/` and `true_only/`) and by
   reading `addons/gd-tools-coverage/coverage.gd`'s `_inject_trackers()` directly.**
   `if_false`/`elif_true`/`match_case` trackers are injected *inside* the branch
   body, so they only fire when that body actually executes -- correct. `if_true`
   falls through to the function's `else` clause in that same code and is
   injected *before* the `if` line itself, so it fires on every evaluation of the
   decision regardless of outcome. The false-branch-only run proves the practical
   consequence: with `run(-2)` as the only call, line 6 (the true-branch body) is
   never hit, but gd-tools' own `coverage.info` still reports `BRDA:5,0,0,1` and
   `BRF:2 BRH:2` -- **100% branch coverage while the true branch's body never
   executed.** gd-tools' branch percentage is not a reliable signal that both
   outcomes of an `if`/`else` were exercised; it can be satisfied on the
   `if_true` side by merely reaching the decision.

## What this does and doesn't establish

- Line coverage on a no-branch case (F010) is accurate, including the source
  hash recorded in `plan.json`.
- Branch coverage exists (contradicting nothing from the earlier survey, which
  only flagged branch coverage as *unverified*, not absent), but its `if_true`
  counter does not mean what a user would reasonably assume it means, and there
  is a separate, confirmed completeness gap for uninitialized declarations.
- Does **not** confirm F008's or F071's findings transfer to a full
  `gd-tools test --coverage` invocation -- F008 and F071 were tested through
  gd-tools' Python API (`generate_plan()`) and its `merge` CLI directly, not
  through an end-to-end test run. That remains a real but separate finding,
  not re-verified here.
- Does **not** re-run F040/F091/F045/F060's real-adapter equivalents (autoload
  timing, await, reload-with-real-instrumentation) -- those remain source-read
  predictions pending their own BP04/BP05-style real runs. Note also that
  `pilot/fixtures/oracles/F040.json`'s claim that gd-tools "rewrites source files
  on disk before Godot ever imports the project" is itself unverified against the
  real tool and contradicts `coverage.gd`'s own doc comment, which describes
  in-memory `reload(true)` instrumentation, not a disk rewrite -- flagged as an
  open correction, not yet fixed in that oracle.
- Does **not** constitute the full tier-0 or tier-1 corpus run -- per
  `implementation-plan.md`, "the first usable contribution is BP04, not
  completion of every catalog case."
