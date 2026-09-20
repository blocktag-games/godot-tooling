# Corpus run against candidate tools — 2026-09-19 / 2026-09-20

BP06's closing item: run the built correctness corpus against the
viable coverage-COLLECTING candidates identified in BP05 (gd-tools-cli
0.4.0, Nano Coverage via its GdUnit4 session hook) and record the
result. See `pilot/adapter-run/corpus-sweep/` for both sweep scripts,
raw TSVs, and reproduction steps.

This document was rewritten after an initial version was reviewed
against the remaining work packages (BP07-BP13). That review found the
first sweep's pass/fail guard could never fail (a substring collision
with GUT's own failure text) and that "30/53 matched" invited reading
as a score rather than a root-cause breakdown. Both are fixed here: the
gd-tools sweep now gates on known-answer controls before writing a
single row, was re-run, and reproduced its prior 53/53 results **byte-
for-byte identical** -- the original data was correct, but it is now
correct-and-verified rather than correct-by-argument. A second sweep
against Nano Coverage was then built and run for the first time,
closing what would otherwise have been a "candidates" (plural) claim
resting on one candidate.

## Scope

- **Group 1 (pure GDScript, 26 fixtures, 53 named oracle inputs)** —
  run in full against BOTH candidates, one invocation per input per
  tool (106 real invocations total, not counting each script's own
  known-answer controls).
- **Group 2 (lifecycle, own mini-projects)** — spot-checked one
  representative (F042, enter/ready/exit-tree) against gd-tools only:
  coverage collection matched exactly (3/3 obligations) in a live
  scene-tree context, not just static function calls. Not spot-checked
  against Nano Coverage. The remaining ~10 Group 2 fixtures are **not
  swept** against either tool — deferred, not assumed clean.
- **Group 3 (harness-dependent, real-tool)** — already run against real
  tools as part of their own construction (each has its own
  `check.py`). Not re-run here; would be redundant, not new evidence.
- **A third coverage-collecting candidate** — does not exist in BP05's
  survey and this sweep does not reopen that question. godot-code-
  coverage was excluded in BP05 for a verified, reproducible
  incompatibility with the pinned Godot 4.7.1 engine, within the
  plan's own one-working-day setup budget. GdUnit4 is a test *runner*,
  not an independent coverage collector — F080 established application-
  behavior parity with GUT as a runner, not coverage parity, and
  gd-tools' own coverage collection is bound to GUT's hooks (never
  wired to GdUnit4). Nano Coverage's *use* of GdUnit4 here is as its
  session-hook integration point, not evidence that GdUnit4 itself
  collects coverage.

## How to read the findings below

Findings are split into two categories per the plan's own rule
("record alternative contracts and defer universal claims; never
derive truth from a favored collector"):

- **Contract-independent**: true regardless of which lines this
  corpus's oracles choose to treat as executable statements. These are
  facts about the tool's own instrumentation mechanism.
- **Contract-dependent**: true only relative to THIS corpus's own
  convention for what counts as an executable statement obligation.
  Each of these names at least one concrete alternative convention a
  different tool or oracle author could reasonably choose instead.

Findings are reported by root cause and affected fixture count, not as
a "matched/total" ratio — inputs were not sampled, several mismatches
share one cause, and a ratio invites exactly the score-like reading
this rewrite is correcting.

## gd-tools-cli 0.4.0 — 13 of 53 inputs affected, 4 root causes

All confirmed by direct inspection of
`gd_tools/addons/gd-tools-coverage/coverage.gd`'s `_inject_trackers()`
(which decides where each tracker call physically lands) plus real
`plan.json`/`coverage.json` output — not inferred from mismatches alone.

### [Contract-independent] 1. A counter labeled `if_true`/`elif_true`/`loop_body` fires on every evaluation of the decision, not on the labeled outcome

`_inject_trackers()` places the tracker for these three branch types
**before** the line, the same placement rule used for an ordinary
statement — so the counter increments whenever the decision/loop
header is reached and evaluated, regardless of which way it resolves.
A line whose ground truth says `if_true: false` or `loop_entered:
false` for a given input still reads as hit, because "reached" and
"specific outcome taken" are the exact same physical counter. This is
true independent of any oracle convention: a counter that is supposed
to represent one specific outcome and instead represents "reached at
all" is a definitional mismatch with its own declared name, not a
matter of taste about what counts as a statement.

Affected: F020, F021, F022 (the `if_true` arm only), F023, F024 (`zero`
input), F026 (`if_true` and `loop_entered` cases), F033, F034, F049 —
9 of the 13 affected inputs.

Contrast: `if_false` (the `else:` branch) and `match_case`/`elif_true`
*when actually taken* are placed **inside** the body they guard — these
counters correctly represent "this outcome happened." Every `if_false`
obligation in this sweep matched cleanly.

### [Contract-independent] 4. Ternary/conditional expressions have zero branch-level tracking

A full `plan.json` branch_type enumeration across this corpus returns
exactly `{elif_true, if_false, if_true, loop_body, match_case}` — no
ternary-related entry exists at all, for any fixture, in any run. F029
was built specifically to demonstrate that a whole-line hit can't
distinguish ternary arms; this sweep confirms that as observed tool
behavior, not a hypothetical gap. The statement-level fact (was the
line reached) tracks fine; which arm executed is invisible to gd-tools
entirely, regardless of how an oracle chooses to model it.

Affected: F029 (both inputs).

### [Contract-dependent] 2. `elif_true`/`match_case`, being taken-only counters, cannot distinguish "never evaluated" from "evaluated and false"

Because these two branch types are injected *inside* their own body
(only firing when actually taken), gd-tools has no way to represent
"this elif/match arm's condition was checked and found false" as
distinct from "this arm was never reached because an earlier one
already matched." Both read as zero on the one counter gd-tools has
for that line.

**This corpus's convention** treats an elif/match-arm's condition line
as a statement obligation independent of its branch obligation — i.e.
"was this line's condition evaluated at all" is asked as a fact
separate from "was this specific outcome taken," per `oracles/F022.json`
and `oracles/F027.json`. **A named alternative**: a tool or oracle that
only ever asks "was this arm's body reached" (collapsing the
statement-vs-branch distinction for arm headers entirely, the way many
line-coverage-only tools do for `else`/`elif` chains generally) would
not register this as any kind of gap at all, because it would never
have asked the question this corpus's obligation schema asks. Under
that alternative convention, this is not a finding — it's simply an
unaskable question. Whether this corpus's finer-grained convention is
the "right" one for a general-purpose benchmark, or an artifact of this
project's own schema design, is left open rather than asserted.

Affected: F022 (`zero`, `none` — missing_hits on later elif lines), F027
(`two`, `other` — missing_hits on earlier non-matching `match_case`
lines) — 4 of the 13 affected inputs.

### [Contract-dependent] 3. Three declaration/header lines have no trackable point in gd-tools' plan at all

- F020 line 4 (`var outcome: int`, no initializer).
- F027 line 4 (`match value:`, the match statement's own header line).
- F035 line 3 (`var _value: int = 0`, a member variable initializer).

**This corpus's convention** treats a variable declaration (with or
without an initializer) and a `match` statement's own header as
executable statement obligations — the reasoning recorded in
`oracles/F001.json` is that these are "real, meaningful declaration
points a coverage report ought to be able to say something about."
**A named alternative**: LCOV's own `DA` record convention (and by
extension most line-coverage tools built around it, including Nano
Coverage — see below) commonly omits a bare declaration line with no
side-effecting initializer expression from its trackable-line set
entirely, on the reasoning that a declaration with no computation has
nothing to "execute" in the sense line coverage measures. Under that
alternative convention, F020's line 4 specifically would not be a gap
at all. F027's `match` header and F035's member initializer (which DOES
have a side-effecting initializer, `= 0`) are less clearly covered by
that alternative and remain closer to contract-independent — included
here under the contract-dependent heading for caution, not because the
alternative cleanly resolves all three the same way.

Affected: F020 (`var outcome: int`), F027 (all three inputs, via the
`match` header), F035 (`default`) — these overlap with findings 1 and
2's affected-input counts above rather than adding new inputs, since
each of these three lines' obligations also register as `missing_hits`
within an input already counted there.

## Nano Coverage (via GdUnit4's session hook) — 6 of 53 inputs affected, 3 root causes

Nano Coverage's coverage-report/lcov.info is a genuine LCOV file,
directly keyed by real source line number (`DA:<line>,<count>`) — no
opaque id-translation table exists the way gd-tools' plan.json requires
one. It emits **zero `BRDA` (branch) records anywhere in its addon
source** (confirmed: `grep -rn "BRDA" .../nano_coverage_godot/` returns
nothing) — it is a pure statement-coverage tool. Every branch-kind
obligation in this corpus (69 across the 53 swept inputs) is therefore
**not applicable** to Nano Coverage, not a `missing_hits` failure —
`run_sweep_nano.py` excludes them before comparing and records the
excluded count per row (`results_nano.tsv`'s `excluded_branch_obligations`
column) so a clean row is never misread as "this fixture had nothing to
find."

### [Contract-independent] 1. An untaken-but-evaluated `elif` header line reports as completely unhit — independently convergent with gd-tools' finding 2

Direct `lcov.info` inspection for F022's `zero` input (`value == 0`,
where `if value > 10` and `elif value > 0` are both evaluated and
false before `elif value == 0` matches): line 5 (the first `if`) shows
`DA:5,1` — hit, correctly, since it's genuinely always evaluated. Line
7 (the first `elif`) shows `DA:7,0` — NOT hit, despite genuinely being
reached and evaluated in this run (`0 > 0` is false, execution
proceeds to the next `elif`). Line 9 (the second elif, condition true)
shows `DA:9,1` — hit, because its body executed.

This is the same underlying shape as gd-tools' finding 2, on a
completely independently built tool using a completely different
instrumentation mechanism (Nano Coverage's tree-sitter-based static
analysis vs. gd-tools' in-memory source-string tracker insertion).
Both land on: the first `if` in a chain gets a "reached regardless of
outcome" line record, but subsequent `elif` headers only register a hit
when their own body executes — an evaluated-but-false `elif` condition
is indistinguishable from an unreached one. This convergence is
stronger evidence that this is a genuinely difficult case to
instrument correctly (plausibly related to how GDScript's `elif` chain
lowers internally) than either tool's behavior alone would be — it is
reported here as contract-independent for that reason, unlike gd-tools'
own version of this same underlying issue, which was filed as
contract-dependent above because gd-tools additionally exposes a
distinguishable statement-vs-branch fact for the first `if` that
Nano Coverage's plain `DA` record does not.

Affected: F022 (`zero`, `none`) — 2 of the 6 affected inputs.

### [Contract-dependent] 2. Match-statement pattern label lines (`1:`, `2:`, `_:`) receive no LCOV record at all when not matched

F027's `lcov.info`, for the `one` input, contains exactly four `DA`
records for `subject.gd`: lines 4 (`match value:`), 6, 8, and 10 (the
three arm bodies) — lines 5, 7, and 9 (the pattern labels themselves)
have **no `DA` record whatsoever**, not even a `DA:<line>,0`. This is a
stronger/cleaner version of gd-tools' finding 2 for the same construct:
gd-tools at least has a `match_case` branch counter for these lines
(taken-only, but present); Nano Coverage's static analysis apparently
does not identify a match pattern label as a trackable statement
location at all.

**This corpus's convention** treats a match pattern label line as a
statement obligation (see `oracles/F027.json`: "reached: the first
pattern is always checked"). **A named alternative**: a tool that
models a `match` statement as a single decision point with N labeled
outcomes (closer to a switch-statement model in other languages, where
individual case labels are not independently instrumented lines) would
never ask this question either — same shape as gd-tools' finding 2's
alternative.

Affected: F027 (`one`, `two`, `other`) — 3 of the 6 affected inputs.

### [Contract-independent] 3. Property getter/setter accessor bodies are entirely absent from coverage tracking

F035's `lcov.info` contains exactly 3 `DA` records total, for lines 11,
12, 13 (the `static func run()` body) — lines 3 (the backing field's
initializer), 6 (the getter's `return _value`), and 8 (the setter's
`_value = v * 2`) have **no `DA` record at all**. This is a broader gap
than gd-tools' version of the same fixture (which only missed line 3,
the initializer — gd-tools DID track the getter and setter bodies at
lines 6 and 8). Nano Coverage's tree-sitter-based static analysis
appears not to identify a property's `get:`/`set(v):` block bodies as
instrumentable statement locations at all, independent of any
convention choice — an implicit accessor body is unambiguously
executable code by any reasonable definition, and it observably runs
(the fixture's own assertion depends on it).

Affected: F035 (`default`) — 1 of the 6 affected inputs.

## What did NOT need reporting as a finding

Four apparent mismatches across both sweeps turned out to be bugs in
the sweep scripts' own translation logic, not tool behavior, and were
fixed before any of the findings above were trusted:

- **gd-tools sweep**: branch-type plan entries were only routed into
  the comparator's `branches` dict, never `hits` — silently reporting
  every decision-header *statement* obligation as unreached. Fixed by
  populating both from the same raw counter (this fix is what actually
  revealed finding 1 above). gd-tools' own internal branch_type label
  for a loop header (`loop_body`) doesn't match this corpus's label for
  the same concept (`loop_entered`) — an aliasing problem between two
  independently-chosen vocabularies, not a behavioral deviation. Fixed
  with an explicit, evidence-documented alias table.
- **gd-tools sweep, discovered on review**: the pass/fail guard checked
  for the substring `"1 passed"` in GUT's stdout, which GUT's own
  failure line (`"0/1 passed."`) also contains — the guard could never
  fail. Fixed to assert the exact expected outcome per input
  (`EXPECTED_GUT_FAILURES`), and the corrected script was re-run in
  full: **the regenerated `results.tsv` is byte-for-byte identical** to
  the one produced under the broken guard. The original 53 rows were
  correct; the guard just wasn't proving it.
- **Nano Coverage sweep**: `build_actual()` only ever built a single
  file's worth of comparator data, silently mis-scoring the second
  bound file in F001 (`loaded.gd` + `unloaded.gd`) and F049
  (`subject.gd` + `dependency.gd`) as `missing_files`. Caught by
  reading the raw `lcov.info` directly and finding a correct `SF:`
  record for both files in both fixtures before trusting the aggregate
  diff. Fixed to build one comparator file entry per distinct file the
  oracle's obligations reference; both fixtures now compare clean.

## Both known-answer control gates passed on every run

Both `run_sweep.py` and `run_sweep_nano.py` now call a `verify_controls()`
function before writing a single sweep row, which raises immediately if
it fails rather than silently producing plausible-looking rows. On
every run reported here, both scripts printed `CONTROL OK` for all of
their controls. See `pilot/adapter-run/corpus-sweep/README.md` for
exactly what each control checks and why.

## Reproduction

See `pilot/adapter-run/corpus-sweep/README.md`. Raw results:
`pilot/adapter-run/corpus-sweep/results.tsv` (gd-tools, 53 rows) and
`results_nano.tsv` (Nano Coverage, 53 rows), one row per fixture/input,
with match status and the exact `false_hits`/`missing_hits` tuples
`comparator.compare()` returned.
