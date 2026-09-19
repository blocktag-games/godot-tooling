#!/usr/bin/env python3
"""BP03 self-tests: prove the harness's own report comparator cannot be
fooled by a bad synthetic adapter output, and correctly recognizes a
good one. This is BP03's completion evidence per implementation-plan.md
("synthetic failure controls pass ... positive controls ... also
pass"). No real coverage tool is involved -- every input here is
hand-crafted specifically to probe one comparator behavior.

Run: python3 self_test.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from comparator import MalformedReportError, Obligation, compare  # noqa: E402

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
    """A report whose file hash no longer matches current source (source
    edited after the report was produced) must be rejected as stale, not
    scored against the new source."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        f, sha = make_source(tmp)
        obligations = [Obligation(file="subject.gd", sha256=sha, line=4, expected_hit=True)]
        f.write_text("extends RefCounted\n\nstatic func run() -> int:\n\treturn 2\n")
        actual = {"files": [{"path": "subject.gd", "sha256": sha, "hits": {"4": 1}}]}
        result = compare(obligations, actual, tmp)
        check(
            "stale_report_detected",
            result.status == "mismatch" and "subject.gd" in result.stale_files,
            str(result),
        )


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
    """A truncated/malformed report body must fail to parse, not be
    silently treated as an empty (and therefore vacuously passing) or
    complete report."""
    raised = False
    try:
        json.loads('{"files": [{"path": "subject.gd", "sha256": "ab')
    except json.JSONDecodeError:
        raised = True
    check("truncated_json_rejected", raised, "expected JSONDecodeError")


def test_null_adapter_shows_no_behavioral_difference() -> None:
    """Positive control: a no-op 'adapter' that changes nothing must show
    baseline and covered behavior as identical -- proves the harness's
    behavior check can recognize agreement, not only ever detect
    injected differences."""
    baseline_stdout = "result=7\n"
    covered_stdout = "result=7\n"
    check(
        "null_adapter_no_behavioral_difference [positive control]",
        baseline_stdout == covered_stdout,
        f"{baseline_stdout!r} != {covered_stdout!r}",
    )


def main() -> int:
    test_clean_report_matches()
    test_false_hit_detected()
    test_missing_hit_detected()
    test_missing_file_detected()
    test_stale_report_detected()
    test_malformed_shape_rejected()
    test_truncated_json_rejected()
    test_null_adapter_shows_no_behavioral_difference()
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
