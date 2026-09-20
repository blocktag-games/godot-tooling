#!/usr/bin/env python3
"""BP03 self-tests: prove the harness's own report comparator, workspace
isolation, and outcome recording cannot be fooled by a bad synthetic
adapter output, and correctly recognize a good one. This is BP03's
completion evidence per implementation-plan.md ("synthetic failure
controls pass ... positive controls ... also pass"). No real coverage
tool is involved -- every input here is hand-crafted specifically to
probe one harness behavior.

Run: python3 self_test.py
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import workspace  # noqa: E402
from comparator import MalformedReportError, Obligation, compare, load_actual_report  # noqa: E402
from outcome import Outcome  # noqa: E402
from runner import run  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def make_source(tmp: Path, body: str = "return 1") -> tuple[Path, str]:
    f = tmp / "subject.gd"
    f.write_text(f"extends RefCounted\n\nstatic func run() -> int:\n\t{body}\n")
    return f, hashlib.sha256(f.read_bytes()).hexdigest()


def test_clean_report_matches() -> None:
    """Positive control: a hand-written correct report must score a full,
    clean match -- proves the comparator can pass, not just reject."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {"4": 1}}]}
        result = compare(obligations, actual, tmp)
        check(
            "clean_report_matches [positive control]",
            result.status == "match" and result.is_clean,
            str(result),
        )


def test_false_hit_detected() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=False)]
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {"4": 1}}]}
        result = compare(obligations, actual, tmp)
        check(
            "false_hit_detected",
            result.status == "mismatch" and ("subject.gd", 4) in result.false_hits,
            str(result),
        )


def test_missing_hit_detected() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {}}]}
        result = compare(obligations, actual, tmp)
        check(
            "missing_hit_detected",
            result.status == "mismatch" and ("subject.gd", 4) in result.missing_hits,
            str(result),
        )


def test_missing_file_detected() -> None:
    """A selected file entirely absent from the report must not be read
    as zero coverage -- it must be a distinct, explicit outcome."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        actual = {"files": []}
        result = compare(obligations, actual, tmp)
        check(
            "missing_file_detected",
            result.status == "mismatch" and "subject.gd" in result.missing_files,
            str(result),
        )


def test_stale_report_detected() -> None:
    """The oracle's expected hash matches current source (the oracle is
    up to date), but the report's OWN declared hash for the file is from
    a different version -- e.g. a cached/stale report from a prior tool
    run. Must be rejected as stale, not scored against current source.
    Kept distinct from test_oracle_stale_source_detected: here the
    oracle is correct and only the report is wrong."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        stale_report_sha = "1" * 64
        actual = {"files": [{"path": "subject.gd", "sha256": stale_report_sha, "hits": {"4": 1}}]}
        result = compare(obligations, actual, tmp)
        check(
            "stale_report_detected",
            result.status == "mismatch"
            and "subject.gd" in result.stale_files
            and "subject.gd" not in result.oracle_stale_files,
            str(result),
        )


def test_oracle_stale_source_detected() -> None:
    """If the oracle's OWN expected sha256 no longer matches the file on
    disk, that is a different problem from a stale report: the oracle is
    bound to the wrong version of the source. Must be flagged distinctly,
    and checked before anything else about the file is trusted."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, current_sha = make_source(tmp)
        stale_oracle_sha = "0" * 64
        obligations = [Obligation(file="subject.gd", sha256=stale_oracle_sha, line=4, expected_hit=True)]
        actual = {"files": [{"path": "subject.gd", "sha256": current_sha, "hits": {"4": 1}}]}
        result = compare(obligations, actual, tmp)
        check(
            "oracle_stale_source_detected",
            result.status == "mismatch" and "subject.gd" in result.oracle_stale_files,
            str(result),
        )


def test_branch_evidence_distinguished_from_hits() -> None:
    """A branch obligation (evidence='branches') and a statement
    obligation (evidence='hits') on the SAME line must be checked
    against separate evidence sources, matching how LCOV keeps DA (line
    hits) and BRDA (branch hits) as distinct record types -- a line can
    be 'reached' independently of whether a specific outcome was
    'taken'."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [
            Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True),  # reached
            Obligation(
                file="subject.gd", sha256=sha, line=4, expected_hit=False,
                evidence="branches", branch_type="if_true",
            ),  # reached, but this outcome was NOT taken
        ]
        actual = {
            "files": [
                {"path": "subject.gd", "sha256": sha, "hits": {"4": 1}, "branches": {"4:if_true": 0}}
            ]
        }
        result = compare(obligations, actual, tmp)
        check(
            "branch_evidence_distinguished_from_hits [positive control]",
            result.status == "match" and result.is_clean,
            str(result),
        )


def test_branch_evidence_missing_branches_dict_reads_as_not_taken() -> None:
    """If a report has no 'branches' entry at all for a file, a branch
    obligation must read as not-taken (was_hit=False), not raise or be
    silently skipped -- absence of branch evidence is itself a fact."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [
            Obligation(
                file="subject.gd", sha256=sha, line=4, expected_hit=True,
                evidence="branches", branch_type="if_true",
            )
        ]
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {"4": 1}}]}  # no "branches" key
        result = compare(obligations, actual, tmp)
        check(
            "branch_evidence_missing_dict_reads_as_not_taken",
            result.status == "mismatch" and ("subject.gd", 4) in result.missing_hits,
            str(result),
        )


def test_obligation_rejects_invalid_evidence() -> None:
    raised = False
    try:
        Obligation(file="subject.gd", sha256="0" * 64, line=4, expected_hit=True, evidence="bogus")
    except ValueError:
        raised = True
    check("obligation_rejects_invalid_evidence", raised, "expected ValueError")


def test_branch_obligation_requires_branch_type() -> None:
    raised = False
    try:
        Obligation(file="subject.gd", sha256="0" * 64, line=4, expected_hit=True, evidence="branches")
    except ValueError:
        raised = True
    check("branch_obligation_requires_branch_type", raised, "expected ValueError")


def test_inconsistent_oracle_hash_rejected() -> None:
    """Two obligations for the same file declaring different sha256
    values is a broken oracle, not a comparable case -- must raise, not
    silently pick one."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [
            Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True),
            Obligation(file="subject.gd", sha256="f" * 64, line=5, expected_hit=True),
        ]
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {"4": 1, "5": 1}}]}
        raised = False
        try:
            compare(obligations, actual, tmp)
        except MalformedReportError:
            raised = True
        check("inconsistent_oracle_hash_rejected", raised, "expected MalformedReportError")


def test_malformed_shape_rejected() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        _, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        raised = False
        try:
            compare(obligations, {"not_files": []}, tmp)
        except MalformedReportError:
            raised = True
        check("malformed_shape_rejected", raised, "expected MalformedReportError")


def test_truncated_json_rejected() -> None:
    """A truncated/malformed report file must fail to load via the
    harness's own load_actual_report(), not be silently treated as an
    empty (and therefore vacuously passing) or complete report. Exercises
    real harness code, not the standard-library json module directly."""
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "report.json"
        bad.write_text('{"files": [{"path": "subject.gd", "sha256": "ab')
        raised = False
        try:
            load_actual_report(bad)
        except MalformedReportError:
            raised = True
        check("truncated_json_rejected", raised, "expected MalformedReportError from load_actual_report")


def test_workspace_isolation_and_restoration_check() -> None:
    """A workspace is a fresh, separate copy of a case directory;
    mutating it must never affect the source, and verify_unchanged()
    must catch a mutation rather than silently pass it."""
    with tempfile.TemporaryDirectory() as case_dir_str:
        case_dir = Path(case_dir_str)
        (case_dir / "subject.gd").write_text("original\n")
        ws = workspace.create(case_dir)
        try:
            check(
                "workspace_is_a_separate_copy",
                ws.root != case_dir and (ws.root / "subject.gd").exists(),
                str(ws.root),
            )
            (ws.root / "subject.gd").write_text("mutated\n")
            check(
                "workspace_mutation_does_not_touch_source",
                (case_dir / "subject.gd").read_text() == "original\n",
                (case_dir / "subject.gd").read_text(),
            )
            unchanged = workspace.verify_unchanged(ws)
            check(
                "verify_unchanged_detects_mutation",
                unchanged.get("subject.gd") is False,
                str(unchanged),
            )
        finally:
            workspace.cleanup(ws)
        check("workspace_cleanup_removes_directory", not ws.root.exists(), str(ws.root))


def test_null_adapter_shows_no_behavioral_difference() -> None:
    """Positive control: running the same no-op subject through two
    separate isolated workspaces (modeling a baseline run and a
    covered-by-a-null-adapter run) must show identical behavior --
    exercised through the real workspace and process-runner
    infrastructure, not two hardcoded strings standing in for a process
    that never actually ran. Proves the pipeline recognizes agreement,
    not only ever injected differences."""
    with tempfile.TemporaryDirectory() as case_dir_str:
        case_dir = Path(case_dir_str)
        (case_dir / "subject.py").write_text("print('result=7')\n")
        ws_baseline = workspace.create(case_dir)
        ws_covered = workspace.create(case_dir)  # the "null adapter": an untouched copy
        try:
            baseline = run([sys.executable, "subject.py"], cwd=str(ws_baseline.root))
            covered = run([sys.executable, "subject.py"], cwd=str(ws_covered.root))
            outcome_baseline = Outcome(
                case_id="null-adapter-baseline",
                command=[sys.executable, "subject.py"],
                exit_code=baseline.exit_code,
                duration_s=baseline.duration_s,
                started_at="self_test",
                status="pass" if baseline.exit_code == 0 else "fail",
            )
            outcome_covered = Outcome(
                case_id="null-adapter-covered",
                command=[sys.executable, "subject.py"],
                exit_code=covered.exit_code,
                duration_s=covered.duration_s,
                started_at="self_test",
                status="pass" if covered.exit_code == 0 else "fail",
            )
            check(
                "null_adapter_no_behavioral_difference [positive control]",
                baseline.stdout == covered.stdout
                and outcome_baseline.status == "pass"
                and outcome_covered.status == "pass",
                f"baseline={baseline.stdout!r} covered={covered.stdout!r}",
            )
        finally:
            workspace.cleanup(ws_baseline)
            workspace.cleanup(ws_covered)


def test_run_kills_entire_process_tree_on_timeout() -> None:
    """F067's ground truth: run()'s timeout must reach a child process
    spawned BY the command it launches (e.g. gd-tools test spawning a
    Godot subprocess), not just the direct child. A plain
    subprocess.run(..., timeout=...) only ever signals the direct child;
    the grandchild is left orphaned and running. Uses two tiny synthetic
    Python scripts (no Godot dependency) so this stays fast and
    deterministic: a parent that spawns a child and then sleeps past the
    timeout, and a child that just sleeps and can be checked for
    liveness afterward via its own recorded PID.
    """
    import os
    import time

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        child_pid_file = tmp / "child.pid"
        child_script = tmp / "child.py"
        child_script.write_text(
            "import os, time, sys\n"
            f"open({str(child_pid_file)!r}, 'w').write(str(os.getpid()))\n"
            "time.sleep(30)\n"
        )
        parent_script = tmp / "parent.py"
        parent_script.write_text(
            "import subprocess, sys, time\n"
            f"subprocess.Popen([sys.executable, {str(child_script)!r}])\n"
            "time.sleep(30)\n"
        )

        result = run([sys.executable, str(parent_script)], cwd=str(tmp), timeout_s=1.5)
        check("run_reports_timeout", result.timed_out, str(result))

        # Give the killed child's PID file a moment to appear if the
        # child were somehow still alive and only just now writing it
        # (it shouldn't be -- this just avoids a race against a false
        # pass on a slow CI machine).
        deadline = time.monotonic() + 2.0
        while not child_pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        check("child_process_pid_was_recorded", child_pid_file.exists(), "child never started")

        if child_pid_file.exists():
            child_pid = int(child_pid_file.read_text())
            # SIGKILL delivery to the process group is not synchronous
            # with os.killpg() returning, and a just-killed process can
            # briefly remain visible to os.kill(pid, 0) as a zombie
            # until its new parent (init, after reparenting) reaps it.
            # Poll briefly rather than checking exactly once -- checking
            # once produced a real, observed flaky failure under system
            # load (the process was reaped a few milliseconds later).
            child_still_alive = True
            liveness_deadline = time.monotonic() + 2.0
            while time.monotonic() < liveness_deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    child_still_alive = False
                    break
                time.sleep(0.05)
            check(
                "child_process_reaped_not_orphaned",
                not child_still_alive,
                f"child pid {child_pid} is still running after run()'s timeout -- "
                "orphaned, exactly the F067 defect this test guards against",
            )


def main() -> int:
    test_clean_report_matches()
    test_false_hit_detected()
    test_missing_hit_detected()
    test_missing_file_detected()
    test_stale_report_detected()
    test_oracle_stale_source_detected()
    test_branch_evidence_distinguished_from_hits()
    test_branch_evidence_missing_branches_dict_reads_as_not_taken()
    test_obligation_rejects_invalid_evidence()
    test_branch_obligation_requires_branch_type()
    test_inconsistent_oracle_hash_rejected()
    test_malformed_shape_rejected()
    test_truncated_json_rejected()
    test_workspace_isolation_and_restoration_check()
    test_null_adapter_shows_no_behavioral_difference()
    test_run_kills_entire_process_tree_on_timeout()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "All BP03 harness self-tests pass: synthetic failure controls and "
        "positive controls both hold."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
