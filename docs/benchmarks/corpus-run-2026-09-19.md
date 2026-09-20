# Corpus run against candidate tools — 2026-09-19

BP06's closing item: run the built correctness corpus against the
viable candidate tools identified in BP05 (gd-tools-cli 0.4.0, GdUnit4
v6.2.1, Nano Coverage via its GdUnit4 session hook) and record the
result. See `pilot/adapter-run/corpus-sweep/` for the sweep script,
raw TSV, and reproduction steps.

## Scope

- **Group 1 (pure GDScript, 26 fixtures, 53 named oracle inputs)** —
  run in full against gd-tools-cli 0.4.0, one invocation per input.
  30/53 matched their oracle exactly; 23/53 mismatched, all traced to
  one of four real, well-understood gd-tools behaviors (below), not to
  a translation bug in the sweep script — the sweep script itself went
  through three iterations before its own bugs stopped producing false
  findings (see git history on `pilot/adapter-run/corpus-sweep/`).
- **Group 2 (lifecycle, own mini-projects)** — spot-checked one
  representative (F042, enter/ready/exit-tree): gd-tools' coverage
  collection matched exactly (3/3 obligations) in a live scene-tree
  context, not just static function calls. The remaining ~10 Group 2
  fixtures are **not swept** — each needs its own hand-wired
  gd-tools+GUT setup (they don't share Group 1's single-project shape),
  and this pass didn't build that for all of them. Deferred, not
  assumed clean.
- **Group 3 (harness-dependent, real-tool)** — already run against real
  tools as part of their own construction (F003, F004, F005, F061,
  F063, F066-F072, F075, F076, F080, F081 each have their own
  `check.py`). Not re-run here; would be redundant, not new evidence.
- **GdUnit4** — established as a test *runner* with application-behavior
  parity to GUT (F080), not as an independent coverage collector.
  gd-tools' coverage collection is bound to GUT's own hook scripts
  (`pre_run_hook.gd`/`post_run_hook.gd`) and was never wired to
  GdUnit4 — running the Group 1 sweep "against GdUnit4" isn't a
  meaningful sentence with the tooling as it exists today.
- **Nano Coverage** — has exactly one working integration
  (`pilot/adapter-run/nano-coverage-gdunit4-f010_straight_line/`, via
  GdUnit4's session hook), re-verified passing as part of this pass
  (4/4 checks). Extending it across the corpus needs a second full
  adapter (translating Nano Coverage's LCOV output and GdUnit4's own
  plan/id scheme into the oracle obligation shape) — not built here.

## Findings against gd-tools-cli 0.4.0

Four real behaviors, all confirmed by direct inspection of
`pilot/gd-tools/.venv/.../gd_tools/addons/gd-tools-coverage/coverage.gd`'s
`_inject_trackers()` (which decides where each tracker call physically
lands) plus real plan.json/coverage.json output, not inferred from the
comparator mismatches alone.

### 1. Single-counter decision headers (`if_true`, `elif_true`, `loop_body`) fire on every evaluation, not on the labeled outcome

This is BP04's original F020 finding, now confirmed corpus-wide and
extended to loop headers. `_inject_trackers()` places the tracker for
these three branch types **before** the line (the same rule used for
ordinary statements) — so the counter increments whenever the
decision/loop header is *reached and evaluated*, regardless of which
way it resolves. A line whose oracle-ground-truth says `if_true: false`
or `loop_entered: false` for a given input still reads as hit,
because reaching-and-evaluating and the specific-outcome-taken are the
exact same physical counter.

Affected in this sweep: F020, F021, F022 (`if_true` only), F023, F024
(`zero` input), F026 (`if_true` and `loop_entered` cases), F033, F034,
F049 — 13 of the 23 mismatches.

**Contrast:** `if_false` (F020/F021's `else:` branch) and `match_case`/
`elif_true` *when taken* are placed **inside** the body they guard —
these counters correctly represent "this specific outcome happened,"
not "this line was reached." The corpus's `if_false` obligations all
matched cleanly (F020, F021 both directions with an else branch).

### 2. `elif_true`/`match_case`, being taken-only counters, cannot distinguish "never evaluated" from "evaluated and false"

The flip side of #1: because these two branch types are injected
*inside* their own body (only firing when actually taken), gd-tools has
**no way at all** to represent "this elif/match arm's condition was
checked and found false" — that state is indistinguishable from "this
arm was never reached because an earlier one already matched." Both
read as zero hits on the one counter gd-tools has for that line.

This was flagged as a known *schema* limitation when F022 was designed
this session ("can't yet distinguish elif never evaluated from elif
evaluated and false") — this run confirms it is not just a schema gap
but a genuine **tool** limitation: no instrumentation strategy gd-tools
currently uses could report the intermediate state even if the schema
supported it.

Affected: F022 (`zero`, `none` inputs — missing_hits on later elif
lines), F027 (`two`, `other` inputs — missing_hits on earlier
non-matching `match_case` lines).

### 3. Some declaration/header lines have no trackable point in gd-tools' plan at all

Three lines across the swept corpus never appear in gd-tools'
`plan.json` — not zero-hit, not present-with-zero, genuinely absent as
a trackable point:

- F020 line 4 (`var outcome: int`, declared with no initializer) — the
  original BP04 finding.
- F027 line 4 (`match value:`, the match statement's own header line).
- F035 line 3 (`var _value: int = 0`, a member variable initializer).

A mechanical comparison correctly scores these as `missing_hits`
(never silently excluded) — that is the comparator working as
intended, not a limitation of the harness. It is, however, a genuine
completeness gap in gd-tools: these lines are real, meaningful
declaration points a coverage report ought to be able to say something
about, and currently cannot.

### 4. Ternary/conditional expressions have no branch-level tracking at all

F029 (`value > 0 else non_positive`) was built specifically to be "the
sharpest demonstration" that a whole-line hit can't distinguish ternary
arms (see `oracles/F029.json`'s own design notes) — this run confirms
that as a real, not just hypothetical, gap: gd-tools' branch_type
vocabulary (`elif_true`, `if_false`, `if_true`, `loop_body`,
`match_case` — enumerated directly from a full `plan.json` scan) has no
ternary-related entry at all. The statement-level fact (was the line
reached) is tracked fine; which arm executed is invisible to gd-tools
entirely.

## What did NOT need reporting as a finding

Two apparent early "mismatches" turned out to be bugs in the sweep
script's own gd-tools-output translation, not gd-tools behavior, and
were fixed before any of the above was trusted:

- Branch-type plan entries were only routed into the `branches` dict,
  never `hits` — silently reporting every decision-header *statement*
  obligation as unreached. Fixed by populating both from the same raw
  counter (see finding #1 above, which this fix is what actually
  revealed).
- gd-tools' own internal branch_type label for a loop header
  (`loop_body`) doesn't match this corpus's independently-chosen label
  for the same concept (`loop_entered`) — an aliasing problem between
  two free-text vocabularies, not a tool defect. Fixed with an explicit
  alias table (`BRANCH_TYPE_ALIASES` in `run_sweep.py`).

## Reproduction

See `pilot/adapter-run/corpus-sweep/README.md`. Raw results:
`pilot/adapter-run/corpus-sweep/results.tsv` (53 rows, one per
fixture/input, with match status and the exact false_hits/missing_hits
tuples `comparator.compare()` returned).

## Review addendum (same day)

A review of these conclusions against the remaining work packages
(BP07-BP13) produced two corrections and one new finding.

### Correction: the sweep's pass-guard was vacuous

`run_sweep.py` accepted a run if stdout contained `"1 passed"`, which
GUT's `0/1 passed.` failure line also contains. A single batch run of
all 53 tests shows 51 pass and 2 fail: `F013/middle_statement_errors`
and `F015/reached_but_not_completed`, the two deliberate runtime-error
inputs (GUT 9.7.1 scores any engine error during a test as a failure).
Nothing was masked, and coverage data is independent of test outcome
(F063), so `results.tsv` stands. The guard now asserts the expected
outcome per input. The sweep was not re-run after this fix.

### Correction: findings 2 and 3 are contract-dependent

Whether `var outcome: int` (no initializer), a `match value:` header,
or a not-taken `elif` line is an executable "statement" is an oracle
CONVENTION, not an engine fact. Other ecosystems' collectors differ on
exactly these. Per the plan's own rule ("record alternative contracts;
never derive truth from a favored collector"), these are deviations
from THIS corpus's contract and must be reported with the alternative
contract beside them before BP09 freezes, not as defects. Finding 1
(a counter labeled `if_true` that fires when the outcome is false) and
finding 4 (no ternary tracking) do not depend on a convention.

Also: "30/53 matched" is not a score. 13 mismatches share one root
cause and inputs were not sampled. Report by root cause.

### New finding: instrumentation shifts runtime error line numbers

gd-tools inserts tracker lines into the in-memory source before
`reload(true)`. Verified directly on F015 with the engine alone:
uninstrumented, the division-by-zero reports `subject.gd:4` (correct);
with `GD_TOOLS_COVERAGE_PLAN` set, the same error reports
`subject.gd:5`. Every diagnostic from a covered run points at the
wrong line, by an offset that grows down the file. No fixture covers
this yet; it bears directly on BP11 (F082-F084).
