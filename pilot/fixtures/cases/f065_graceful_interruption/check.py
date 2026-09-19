#!/usr/bin/env python3
"""BP02 ground-truth check for F065: interrupts subject.py at its
MARKER_PARTIAL_WRITTEN point and verifies the termination contract --
no finished-looking final report can exist, and the partial artifact is
retained and still labeled partial. Run: python3 check.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "harness"))
from runner import run_and_terminate_on_marker  # noqa: E402

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    subject = str(Path(__file__).parent / "subject.py")
    with tempfile.TemporaryDirectory() as d:
        out_dir = Path(d)
        result = run_and_terminate_on_marker(
            cmd=[sys.executable, subject, str(out_dir)],
            cwd=str(Path(__file__).parent),
            marker="MARKER_PARTIAL_WRITTEN",
            timeout_s=10,
        )
        check("process_was_terminated", result.killed, str(result))
        check("terminated_by_signal", (result.exit_code or 0) < 0, f"exit_code={result.exit_code}")
        check(
            "no_finished_report_exists",
            not (out_dir / "report.json").exists(),
            "report.json exists despite mid-write termination -- a finished-looking artifact leaked",
        )
        partial = out_dir / "report.json.tmp"
        check("partial_artifact_retained", partial.exists(), "report.json.tmp missing")
        if partial.exists():
            data = json.loads(partial.read_text())
            check(
                "partial_artifact_labeled_partial",
                data.get("status") == "partial",
                f"status={data.get('status')!r}",
            )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print("F065 ground truth confirmed: interruption leaves no finished-looking artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
