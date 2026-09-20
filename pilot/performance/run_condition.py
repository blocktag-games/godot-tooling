"""BP07/BP10: the generic condition runner. Given a candidate, a
workload, and a condition (B0/B1/C), builds a fresh scratch project
(candidates.setup_scratch_project -- clears any prior .godot cache
identically across every condition, per candidates.py's shader-cache
decision), invokes that candidate's real test-runner command for that
condition, and measures PROCESS INTERVAL wall time: "Immediately before
process creation to process exit/reaping," per docs/benchmarks/
performance-protocol.md's exact phase-boundary definition -- not
in-process time, not a phase the tool itself reports.

THIS MODULE IS WRITTEN BUT HAS NOT BEEN RUN. Calling run_condition()
for any real (candidate, workload, condition) combination produces the
first actual timing measurement of this study -- that is BP07's pilot
itself, not preparation, and it has been deliberately left for an
explicit go-ahead rather than run as part of building this file. Only
pilot/performance/verify_workloads.py (raw engine, no coverage tool,
correctness only) and pilot/performance/harness_control/self_test.py
(behavior-only) have actually been executed during BP07-09 preparation.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from candidates import GD_TOOLS, NANO_COVERAGE, REPO_ROOT, CandidateConfig, GODOT_BIN, setup_scratch_project

SCRATCH_ROOT = Path("/tmp/perf-run")  # never inside the repo; never pilot/fixtures/ in place


@dataclass
class ConditionResult:
    candidate: str
    workload: str
    condition: str
    process_interval_seconds: float
    exit_code: int
    stdout: str
    stderr: str


def _run_gd_tools(scratch_dir: Path, workload: str, condition: str) -> tuple[int, str, str]:
    import os
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    gd_tools_bin = str(REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools")
    cmd = [gd_tools_bin, "test", "--test", f"test_{workload}"]
    if condition == "C":
        cmd.insert(2, "--coverage")
    result = subprocess.run(cmd, cwd=str(scratch_dir), env=env, capture_output=True, text=True, timeout=120)
    return result.returncode, result.stdout, result.stderr


def _run_nano_coverage(scratch_dir: Path, workload: str, condition: str) -> tuple[int, str, str]:
    import os
    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run(
        ["bash", "addons/gdUnit4/runtest.sh", "-a", f"tests_gdunit/test_{workload}.gd"],
        cwd=str(scratch_dir), env=env, capture_output=True, text=True, timeout=120,
    )
    return result.returncode, result.stdout, result.stderr


def run_condition(candidate: CandidateConfig, workload: str, condition: str) -> ConditionResult:
    """Runs ONE process for ONE (candidate, workload, condition) triple
    and returns its process-interval elapsed time. Does not loop, does
    not repeat, does not aggregate -- the pilot/study schedule (session/
    block structure, repetition, ordering) is a separate, not-yet-built
    layer on top of this single-shot primitive, per performance-
    protocol.md's block/session structure.
    """
    scratch_dir = SCRATCH_ROOT / f"{candidate.name}-{workload}-{condition}"
    setup_scratch_project(candidate, condition, scratch_dir)

    # Import cache must exist before a timed run -- the fresh-import
    # cost is W14's own workload, not something to fold into every
    # other workload's timing by accident.
    subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(scratch_dir), "--import"],
        capture_output=True, timeout=60,
    )

    start = time.perf_counter()
    if candidate.name == "gd-tools":
        exit_code, stdout, stderr = _run_gd_tools(scratch_dir, workload, condition)
    elif candidate.name == "nano-coverage":
        exit_code, stdout, stderr = _run_nano_coverage(scratch_dir, workload, condition)
    else:
        raise ValueError(f"unknown candidate: {candidate.name}")
    elapsed = time.perf_counter() - start

    return ConditionResult(
        candidate=candidate.name,
        workload=workload,
        condition=condition,
        process_interval_seconds=elapsed,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
    )


if __name__ == "__main__":
    raise SystemExit(
        "run_condition.py is a library for the pilot/study driver, not a "
        "script to invoke directly. Calling run_condition() is the actual "
        "start of BP07's pilot -- explicitly not done as part of writing "
        "this file. See pilot/performance/README.md for what has and has "
        "not been executed."
    )
