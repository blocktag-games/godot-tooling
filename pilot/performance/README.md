# BP07-BP09 preparation (2026-09-20)

Everything in this directory is **preparation for execution**, per an
explicit instruction not to begin the actual performance study yet.
This file states plainly what has and has not been run, since that
boundary was flagged mid-session as easy to blur by accident.

## What has actually been executed

Three things, all deliberately outside the study's evidentiary record:

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

## What has NOT been executed

**`run_condition.py`'s `run_condition()` function has never been
called for a real (candidate, workload, condition) triple.** This is
the actual timing harness -- it invokes a real `gd-tools test` or
`GdUnit4 runtest.sh` and measures process-interval wall time. Calling
it even once produces the first real number of this study. The module
refuses to run standalone specifically to make this boundary explicit
in code, not just in this README.

No pilot sessions, no calibration, no B0/B1/C comparison, no candidate
has been timed under coverage or otherwise. `docs/benchmarks/
performance-eligible-cells.tsv`'s cells are enumerated but none have
been run.

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
  **Input sizes in these files are placeholders, explicitly marked as
  such, pending the pilot's own calibration.**
- **`candidates.py`** -- per-candidate configuration, including a
  real finding from reading source (not assumed): gd-tools has a
  genuine B1 mode (autoload registered, `GD_TOOLS_COVERAGE_PLAN`
  unset); Nano Coverage has none (its GdUnit4 hook instruments
  unconditionally on registration) -- never synthesized, per the
  protocol's explicit warning against doing so.
- **`run_condition.py`** -- the single-shot condition runner. Written,
  syntax-checked, its scratch-project setup exercised -- never called
  for a real timed run.

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

## What remains before BP10 can start

1. **The pilot itself** (BP07): calibrate each workload's fixed input
   size against B0 timing (1-5s target per the protocol), replacing
   `tests_gut/tests_gdunit`'s placeholder constants with frozen values.
   This is real execution, gated on the machine-readiness item below.
2. **Machine readiness** (see `implementation-plan.md`'s BP10 row):
   CPU governor still `powersave`, and as of this preparation pass
   Firefox, another project's live GUT/test-runner process, and four
   of that project's background services were all running on this
   machine. None of this has been touched by this session. Verify
   quiescence (a measured idle-CPU% check, not an assumption) before
   the pilot runs, not just before BP10's main study.
3. Harness cross-checks and the observer matrix (BP08) -- native
   `perf` profiling is unavailable on this machine (not installed,
   kernel `perf_event_paranoid=3`, no sudo in this session); to be
   marked unavailable and worked around, or installed by the user.
