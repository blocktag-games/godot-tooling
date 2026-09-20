"""BP07/BP10: the generic condition runner. Given a candidate, a
workload, and a condition (B0/B1/C), builds a fresh scratch project
(candidates.setup_scratch_project -- clears any prior .godot cache
identically across every condition, per candidates.py's shader-cache
decision), invokes that candidate's real test-runner command for that
condition, and measures PROCESS INTERVAL wall time: "Immediately before
process creation to process exit/reaping," per docs/benchmarks/
performance-protocol.md's exact phase-boundary definition -- not
in-process time, not a phase the tool itself reports.

`extra_env` lets a caller override a workload's input size via the
PERF_W03_N / PERF_W05_* / PERF_W11_* environment variables the
tests_gut/tests_gdunit files read (see their module comments) --
used by calibrate.py's search for a fixed size landing B0's WORK TIME
(not process time -- see the "third pass" postmortem in pilot/
performance/README.md) in the protocol's target 1-5s window. The
frozen size is authoritatively recorded in calibration_result.json,
which run_pilot.py loads directly and passes as extra_env for every
real pilot run -- NOT via the GDScript test wrappers' own DEFAULT_*
fallback constants, which exist only for manual/standalone invocation
and are kept in sync by hand (a real bug hit once already: see
`_DEFAULT_W03_N` etc. below).

**Corrected 2026-09-20, second Fable review pass (the first pilot run
was invalid -- see candidates.py's module docstring and pilot/
performance/README.md's postmortem for the full story):**

1. Uses pilot/harness/runner.py's run() (now extended with an optional
   `env` parameter) for the actual subprocess invocation, instead of a
   bespoke subprocess.run(..., timeout=...) call that did not catch
   subprocess.TimeoutExpired at all -- a hang would have raised through
   and killed the whole pilot sweep with no row recorded, contradicting
   run_pilot.py's own "retain every attempt" design. runner.run() is
   the already-tested, F067-fixed process-group-safe primitive.
2. `behavior_ok` now requires POSITIVE evidence that the workload
   actually ran and passed -- not just `exit_code == 0`. The first
   version's bare exit-code check could not distinguish "the test ran
   and passed" from "zero tests were found and the runner exited 0
   anyway" -- exactly BP06's own documented F064 finding about GUT,
   and exactly the bug that made every row of the first pilot run
   meaningless (the actual root cause was a missing file copy in
   candidates.py, but this check is a second, independent line of
   defense against the same failure SHAPE recurring for a different
   reason). Uses the same stdout-substring patterns already proven in
   pilot/adapter-run/corpus-sweep/run_sweep.py and run_sweep_nano.py.
3. For condition "C" specifically, also checks that a real coverage
   artifact was produced (coverage.json with at least one tracked file
   for gd-tools; a non-empty lcov.info for Nano Coverage) -- recorded
   as a SEPARATE field (coverage_artifact_ok), not folded into
   behavior_ok, so the two facts ("did the test pass" and "did the
   collector actually produce output") stay independently visible
   rather than silently conflated.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from candidates import REPO_ROOT, CandidateConfig, GODOT_BIN, setup_scratch_project

sys.path.insert(0, str(Path(__file__).parent.parent / "harness"))
from runner import run as safe_run  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from verify_workloads import w03_reference, w11_reference  # noqa: E402

SCRATCH_ROOT = Path("/tmp/perf-run")  # never inside the repo; never pilot/fixtures/ in place

# Mirrors of tests_gut/test_workloads.gd's DEFAULT_* constants -- kept in
# sync by hand (GDScript cannot import this Python module or vice
# versa). Used ONLY to compute the independent expected-value oracle
# below when a caller doesn't override the size via extra_env; the
# GDScript side is still the single source of truth for what size
# actually runs when no override is given.
_DEFAULT_W03_N = 15667413
_DEFAULT_W11_N_STEPS = 1671580
_DEFAULT_W11_SEED = 12345


def _read_work_time_seconds(scratch_dir: Path, workload: str) -> float | None:
    # gd-tools' CLI filters/discards the child Godot process's raw
    # stdout/stderr entirely (confirmed directly -- a stdout print
    # marker never survived it even on a passing run), so the test
    # wrappers write this to a file in the scratch project instead;
    # works identically for both runners.
    path = scratch_dir / f"work_time_{workload}.txt"
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip()) / 1_000_000
    except ValueError:
        return None


@dataclass
class ConditionResult:
    candidate: str
    workload: str
    condition: str
    process_interval_seconds: float
    exit_code: int | None
    behavior_ok: bool                  # the workload actually ran and its own assertion passed
    coverage_artifact_ok: bool | None  # None when not applicable (B0/B1); True/False for C
    timed_out: bool
    stdout: str
    stderr: str
    # BP08 (added after a review of the BP07 pilot noted the untimed
    # --import step's own outcome was silently discarded): if this step
    # times out or fails, the timed run below still proceeds against a
    # stale/partial import cache and its cost would silently leak into
    # process_interval_seconds. Recorded so that scenario is visible in
    # the data rather than only in a log nobody reads. These fields did
    # not exist during the SECOND pilot pass -- that run's import step's
    # outcome was never actually checked or recorded (unknown, not
    # assumed clean). The current (third) pilot_results.tsv DOES have
    # these columns populated (0/False for every real row, confirmed).
    import_exit_code: int | None = None
    import_timed_out: bool = False
    # BP07 remediation (added after a review found the pilot calibrated
    # total PROCESS time, dominated by a ~3.5s startup floor, instead of
    # the catalog's "1-5 seconds of USEFUL FIXED WORK"): an in-process
    # monotonic timer around each workload's own fixed-work call, written
    # by the test wrapper to a file in the scratch project (see
    # _read_work_time_seconds below -- print() doesn't survive gd-tools'
    # own stdout filtering, confirmed directly) and read back here. None
    # for W01 (no useful work is defined for it) or if the wrapper didn't
    # write the file (e.g. the run crashed first).
    work_time_seconds: float | None = None


def _gd_tools_behavior_ok(stdout: str) -> bool:
    # Matches the exact pattern proven in corpus-sweep/run_sweep.py --
    # requires the POSITIVE "all tests passed" message, not merely a
    # zero exit code (F064: GUT exits 0 on zero tests found too).
    return "All 1 test(s) passed" in stdout


def _nano_coverage_behavior_ok(stdout: str) -> bool:
    # Matches the exact pattern proven in BP06's F080/corpus-sweep work.
    return "1 test cases" in stdout and "0 errors" in stdout and "0 failures" in stdout


def _gd_tools_coverage_artifact_ok(scratch_dir: Path) -> bool:
    coverage_path = scratch_dir / ".gd-tools/coverage/coverage.json"
    if not coverage_path.exists():
        return False
    try:
        data = json.loads(coverage_path.read_text())
    except json.JSONDecodeError:
        return False
    return len(data.get("files", [])) > 0


def _nano_coverage_artifact_ok(scratch_dir: Path) -> bool:
    lcov_path = scratch_dir / "coverage-report/lcov.info"
    return lcov_path.exists() and lcov_path.stat().st_size > 0


def run_condition(
    candidate: CandidateConfig,
    workload: str,
    condition: str,
    extra_env: dict[str, str] | None = None,
    scratch_label: str | None = None,
) -> ConditionResult:
    """Runs ONE process for ONE (candidate, workload, condition) triple
    and returns its process-interval elapsed time. Does not loop, does
    not repeat, does not aggregate -- the pilot/study schedule (session/
    block structure, repetition, ordering) is a separate layer on top
    of this single-shot primitive, per performance-protocol.md's
    block/session structure.
    """
    extra_env = extra_env or {}
    scratch_dir = SCRATCH_ROOT / (scratch_label or f"{candidate.name}-{workload}-{condition}")
    setup_scratch_project(candidate, condition, scratch_dir)

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    env.update(extra_env)

    # Independent expected-value oracle: compute the reference result in
    # PYTHON (verify_workloads.py's w03_reference/w11_reference, already
    # cross-checked against the raw engine with no coverage tool
    # involved) for whatever size THIS run actually uses -- including
    # calibration probes at non-default sizes, not just the final frozen
    # default -- and hand it to the GDScript test wrapper so it can
    # assert exact equality instead of a shape-only check ("size==5",
    # "has key 'score'") that a wrong bucket count or wrong final score
    # would pass right through.
    #
    # Written to a FILE in the scratch project, not an environment
    # variable: a large-n W11 calibration probe (n_steps=2,000,000) hits
    # roughly 32,000 milestones, a ~270KB JSON blob that exceeds Linux's
    # per-argument/environment-variable size limit (MAX_ARG_STRLEN,
    # 128KB) and made subprocess.Popen fail outright with EINVAL/E2BIG
    # -- confirmed directly during recalibration, not assumed. A file
    # has no comparable size limit.
    if workload == "w03":
        n = int(env.get("PERF_W03_N", _DEFAULT_W03_N))
        (scratch_dir / "expected_w03.json").write_text(json.dumps(w03_reference(n)))
    elif workload == "w11":
        n_steps = int(env.get("PERF_W11_N_STEPS", _DEFAULT_W11_N_STEPS))
        seed_value = int(env.get("PERF_W11_SEED", _DEFAULT_W11_SEED))
        (scratch_dir / "expected_w11.json").write_text(json.dumps(w11_reference(n_steps, seed_value)))

    # Import cache must exist before a timed run -- the fresh-import
    # cost is W14's own workload, not something to fold into every
    # other workload's timing by accident.
    import_result = safe_run(
        [str(GODOT_BIN), "--headless", "--path", str(scratch_dir), "--import"],
        cwd=str(scratch_dir), timeout_s=60, env=env,
    )
    if import_result.timed_out or import_result.exit_code != 0:
        print(
            f"WARNING: untimed --import step for {candidate.name}/{workload}/{condition} "
            f"did not complete cleanly (exit={import_result.exit_code}, timed_out={import_result.timed_out}) "
            f"-- the timed run below proceeds against a possibly stale/partial import cache.",
            file=sys.stderr,
        )

    if candidate.name == "gd-tools":
        gd_tools_bin = str(REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools")
        cmd = [gd_tools_bin, "test", "--test", f"test_{workload}"]
        if condition == "C":
            cmd.insert(2, "--coverage")
    elif candidate.name == "nano-coverage":
        cmd = ["bash", "addons/gdUnit4/runtest.sh", "-a", f"tests_gdunit/test_{workload}.gd"]
    else:
        raise ValueError(f"unknown candidate: {candidate.name}")

    result = safe_run(cmd, cwd=str(scratch_dir), timeout_s=120, env=env)

    if candidate.name == "gd-tools":
        ok = _gd_tools_behavior_ok(result.stdout)
        artifact_ok = _gd_tools_coverage_artifact_ok(scratch_dir) if condition == "C" else None
    else:
        ok = _nano_coverage_behavior_ok(result.stdout)
        artifact_ok = _nano_coverage_artifact_ok(scratch_dir) if condition == "C" else None

    work_time_seconds = _read_work_time_seconds(scratch_dir, workload)

    return ConditionResult(
        candidate=candidate.name,
        workload=workload,
        condition=condition,
        process_interval_seconds=result.duration_s,
        exit_code=result.exit_code,
        behavior_ok=(ok and not result.timed_out),
        coverage_artifact_ok=artifact_ok,
        timed_out=result.timed_out,
        stdout=result.stdout,
        stderr=result.stderr,
        import_exit_code=import_result.exit_code,
        import_timed_out=import_result.timed_out,
        work_time_seconds=work_time_seconds,
    )
