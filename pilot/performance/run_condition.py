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
used by calibrate.py's search for a fixed size landing B0 in the
protocol's target 1-5s window, BEFORE that size is frozen into the
DEFAULT_* constants every subsequent run uses with no override needed.

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

SCRATCH_ROOT = Path("/tmp/perf-run")  # never inside the repo; never pilot/fixtures/ in place


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
    # not exist during the 200-row BP07 pilot, so its import step's
    # outcome was never actually checked or recorded (unknown, not
    # assumed clean) -- committed pilot_results.tsv rows predate these
    # columns and read back as empty via csv.DictReader, not 0/False.
    import_exit_code: int | None = None
    import_timed_out: bool = False


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
    )
