# BP07-BP09 (2026-09-20)

This file states plainly what has and has not been run, since that
boundary was flagged mid-session as easy to blur by accident. Execution
began 2026-09-20; see "Postmortem: the first pilot run was invalid"
below before trusting anything in `pilot_results.tsv` from before that
section's fix commit.

## Postmortem: the first pilot run was invalid

The first full 200-run BP07 pilot sweep measured **zero actual test
executions**. Both gd-tools/GUT and Nano Coverage/GdUnit4 ran, found no
test files, and exited 0 -- this is GUT's own documented BP06 failure
mode (F064: exit code 0 does not mean tests ran), reproduced here.
`run_condition.py`'s `behavior_ok` check at the time was only
`exit_code == 0`, too weak to catch it. The pilot ran to completion,
`pilot_report.py` produced numbers, and everything looked superficially
fine until an adversarially-instructed review sub-agent (per this
project's "spawn a review sub-agent after each phase" practice)
actually read `.gd-tools/results.xml` (`tests="0"`) and the GdUnit4
Godot logs (`"Given directory or file does not exists: tests_gdunit/
test_w11.gd"`, `"No test cases found, abort test run!"`).

Root cause: `candidates.py`'s `setup_scratch_project()` copied
`workloads/` and `drivers/` into each scratch project but never copied
`tests_gut/`/`tests_gdunit/` -- the directories containing the actual
test files each runner was told to execute. Fixed by adding
`test_source_dir`/`test_dest_name` fields to `CandidateConfig` and
having `setup_scratch_project()` actually copy them (gd-tools' default
`test_dirs = ["test", "tests"]`, read from `gd_tools/config.py`, means
the destination for gd-tools specifically must be named `tests`, not
`tests_gut`).

The same review found two further issues, fixed alongside it:

- **Nano Coverage's B0 was not truly "collector absent."** Addon
  sources were keyed per-candidate, not per-condition, so the
  `nano_coverage_godot` extension loaded even under B0 (confirmed via a
  scratch project's `extension_list.cfg` and a `"[NanoCoverage] Editor
  classes registered."` log line under a B0 run). Fixed by
  restructuring `addon_sources_by_condition` to a per-condition
  mapping; Nano Coverage's B0 now copies only `gdUnit4`.
- **Timeouts were never caught.** `run_condition.py` had no
  `subprocess.TimeoutExpired` handling at all, so a single hang would
  have killed the whole sweep with no row recorded, contradicting the
  protocol's "retain every attempt" rule. Fixed by extending
  `pilot/harness/runner.py`'s already-tested `run()` with an optional
  `env` parameter and routing both the `--import` step and the timed
  invocation through it (reusing the existing process-group-safe
  timeout/kill logic rather than reimplementing it).

A related, self-inflicted false finding: while diagnosing the above (before
the fix), a manual probe of W03 at n=100,000 vs n=10,000,000 showed no
timing difference, and was misread as "fixed startup overhead
dominates completely" -- that was actually just confirming zero tests
ran regardless of `n`. This false claim was briefly written into
`calibration_result.json` and the test-wrapper module comments as if
genuine; it has been retracted from all of them. Once the real fix was
in, the same diagnostic was re-run honestly and gave a real difference
(n=1 to 10,000,000 changed elapsed time meaningfully), which surfaced a
second, independent bug in `calibrate.py` itself: see "Design decisions
locked in during preparation" below for the proportional-vs-affine
calibration fix and the real Godot engine-crash limit found while
fixing it.

`behavior_ok` now requires positive evidence a test actually ran and
passed (`"All 1 test(s) passed"` for gd-tools; `"1 test cases"` + `"0
errors"` + `"0 failures"` for Nano Coverage), not just exit code 0, and
condition C additionally checks a real coverage artifact was produced
(`coverage_artifact_ok`).

## What has actually been executed

1. **`validate_analyze.py`** -- pure math on synthetic, fabricated
   numbers (a Monte Carlo simulation with a known planted ratio). No
   Godot, no coverage tool, no real timing. Confirms the analysis
   pipeline (`analyze.py`) recovers a known truth and that its 95% CI
   has close-to-nominal coverage (observed: 949/1000 = 0.949).
2. **`harness_control/self_test.py`** -- ran the five tiny harness-
   control workloads (W00/W02/W17/W18/W19) once each to confirm exact
   behavior (exit codes, byte-for-byte output). Pure Python, no Godot.
3. **`verify_workloads.py`** -- ran the four primary workloads (W01,
   W03, W05, W11) once each against the RAW PINNED ENGINE, with **no
   coverage tool involved at all** -- not gd-tools, not Nano Coverage,
   not even GUT or GdUnit4. Confirms each workload's fixed-work
   definition produces a correct, independently-verified result. No
   timing was recorded by this script.

Also verified without spawning any process: `candidates.py`'s
`setup_scratch_project()` builds a correct scratch project (right
files, right addons, right `project.godot` fragment) for all five real
(candidate, condition) combinations -- pure filesystem setup.

## Execution status

`run_condition.py`'s `run_condition()` has now been called for real,
repeatedly: manual smoke tests of every (candidate, condition)
combination, `calibrate.py`'s probes, and the BP07 pilot sweep
(`run_pilot.py`, writing `pilot_results.tsv`). See the postmortem above
for the first invalid sweep and its fix. The corrected sweep's results
are only trustworthy from the fix commit onward -- check
`pilot_results.tsv`'s `behavior_ok`/`coverage_artifact_ok` columns
directly rather than assuming a clean run.

## What's built

- **`analyze.py`** -- the paired log-ratio geometric-mean overhead
  estimator with a Student-t CI on session means, implementing
  `docs/benchmarks/performance-protocol.md`'s Statistical Analysis
  section exactly. Validated (see above), not yet fed real data.
- **`harness_control/`** -- W00 (no-op), W02 (straight-line
  arithmetic, analytically checkable), W17 (log volume, burst/chunked),
  W18 (wait interval), W19 (memory lifetime). All behavior-verified.
- **`workloads/`** -- the four primary workloads' FIXED-WORK
  definitions (W01 empty app, W03 branch-heavy logic, W05 signals/
  deferred dispatch, W11 representative scene app), each with an
  independently-verified correct implementation. One source per
  workload, shared across both candidates -- no fixture rewritten to
  suit a particular collector, per this project's standing rule.
- **`drivers/`** -- standalone SceneTree drivers used only by
  `verify_workloads.py`'s raw-engine correctness check. Not used by
  the timed harness (see `tests_gut/`/`tests_gdunit/` below for why).
- **`tests_gut/test_workloads.gd`**, **`tests_gdunit/test_w0*.gd`** --
  the actual test-runner wrappers `run_condition.py` will invoke.
  Calling each workload's function directly inside a GUT/GdUnit4 test
  is already "after the first idle frame" for free (the coverage
  autoload/hook's own init runs during the test session's startup,
  before any test body executes) -- the drivers' `call_deferred`
  pattern is specific to having no test-runner session ahead of it.
  **Input sizes are calibrated and FROZEN as of 2026-09-20** (second,
  corrected calibration pass -- see the postmortem above).
- **`candidates.py`** -- per-candidate configuration, including a
  real finding from reading source (not assumed): gd-tools has a
  genuine B1 mode (autoload registered, `GD_TOOLS_COVERAGE_PLAN`
  unset); Nano Coverage has none (its GdUnit4 hook instruments
  unconditionally on registration) -- never synthesized, per the
  protocol's explicit warning against doing so.
- **`run_condition.py`** -- the single-shot condition runner, now
  exercised for real (see "Execution status" above) with positive-
  evidence behavior checks and process-group-safe timeout handling.
- **`calibrate.py`** -- two-point affine-fit calibration (`elapsed =
  floor + slope*n`), replacing an earlier, wrong proportional-scaling
  search. See the postmortem above for why proportional scaling fails
  against a fixed startup floor, and for the real Godot engine-crash
  limit (5,000,000 queued deferred calls exhausts the message queue and
  SIGSEGVs the engine) found while recalibrating W05.

## Design decisions locked in during preparation

- **Shader-cache state**: cleared identically before every condition
  for every candidate (never pre-warmed selectively), so GdUnit4's
  heavier boot cost cancels in the paired ratio rather than risking an
  invisible B0-vs-C asymmetry.
- **Each candidate gets its own no-coverage baseline under its own
  runner** (GUT for gd-tools, GdUnit4 for Nano Coverage) -- runner cost
  is never mistaken for coverage cost.
- **Fresh import cache is built before every timed run**, outside the
  timed interval -- W14 (fresh import) is its own workload; folding
  that cost into every other workload's number would be a measurement-
  boundary error the protocol explicitly warns against.

## BP07 and BP08 status

Both done as of 2026-09-20 (see git history for the corrections each
went through after adversarial review). BP07: the pilot itself,
calibrated and frozen input sizes, valid 200-row `pilot_results.tsv`.
BP08: harness timing validation, an independent timing cross-check,
one available capture (`cProfile` of the harness, since native `perf`
remains unavailable on this machine -- not installed, kernel
`perf_event_paranoid=3`, no sudo in this session), and the reduced H/C
pilot observer matrix at `docs/benchmarks/pilot-observer-matrix.tsv`
(P unavailable for the reason recorded there, not simply "not tried").
Machine quiescence is a BP10 requirement (the controlled main study)
only, not a precondition for either of these phases.

## Known confounds in this pilot's numbers (independent review, 2026-09-20)

A second review (after the corrected pilot re-run) confirmed the 200
rows are valid -- randomization matches the recorded seeds exactly,
input sizes are identical across conditions within every block, all 20
eligible cells are present with none synthesized or skipped, and the
process-interval timing boundary matches the protocol's definition.
It also surfaced real, non-blocking limitations to carry forward:

- **Percentage overhead is not comparable across candidates.** gd-tools'
  B0 floor (~3.5-4.2s: its Python CLI plus an internal redundant
  `--import` launch of its own) is roughly 2x nano-coverage's B0 floor
  (~1.7-2.5s: `bash runtest.sh` plus a windowed, non-headless GdUnit4
  run). The same absolute added cost therefore yields a larger
  percentage for whichever candidate has the smaller floor -- e.g. w03
  shows gd-tools at +206% vs nano-coverage at +269% by percentage, but
  gd-tools' absolute added cost (~8.45s) is actually *larger* than
  nano-coverage's (~6.48s). `pilot_report.py` now prints absolute
  deltas alongside ratios for this reason; compare deltas across
  candidates, never percentages.
- **Source scope instrumented differs slightly between tools.** Nano
  Coverage's lcov output covers 13 files (workloads/, drivers/, and
  tests_gdunit/); gd-tools' coverage plan covers 9 (workloads/ and
  drivers/ only, excluding its own tests dir). The extra files are
  trivial in size but the scopes are not byte-identical.
- **Pilot-only randomization is not the main-study's AB/BA balancing.**
  `run_pilot.py` intentionally skips the protocol's item-4 cross-cell
  shuffle and AB/BA balance for this pilot (see its own module
  comment) -- the realized per-cell orders are visibly imbalanced in
  places (e.g. nano-coverage/w03 had B0 first in 8/10 blocks). Fine for
  an exploratory pilot; BP10's main study must implement real
  balancing, not reuse this shuffle.
- **The untimed `--import` step's own outcome is not recorded** in
  `run_condition.py` -- if it timed out or failed, the run would
  proceed silently and the timed interval would then include leaked
  import cost. Did not occur in this pilot (all 200 rows behavior_ok).
  Worth capturing explicitly before BP10.

None of these bias the B0-vs-C ratio *within* a candidate (the thing
this study actually estimates), so the pilot's 200 rows stand as valid
exploratory data. They matter for BP10's design and reporting.

## What remains before BP10 specifically can start

**Machine readiness** (see `implementation-plan.md`'s BP10 row): CPU
governor still `powersave`, and Firefox, another project's live GUT/
test-runner process, and four of that project's background services
have been observed running on this machine (most recently 2026-09-20).
None of this has been touched by this session. This gate applies to
BP10's controlled main study only, not to BP07-BP09.
