#!/usr/bin/env python3
"""BP08 preparation: behavior checks for the harness-control workloads
(W00, W02, W17, W18, W19), per each workload's behavior_check column in
docs/benchmarks/workload-catalog.tsv. Runs each ONCE with known
arguments and verifies EXACT expected behavior -- this is functional
verification that the workloads are correct, not the calibration or
pilot data collection BP08 itself performs. No timing is recorded or
analyzed here.

Run: python3 self_test.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def test_w00_noop() -> None:
    result = subprocess.run(
        [PY, str(HERE / "w00_noop.py"), "7", "hello-w00"],
        capture_output=True, text=True, timeout=10,
    )
    check("w00_exit_code_exact", result.returncode == 7, str(result.returncode))
    check("w00_stdout_exact", result.stdout == "hello-w00", repr(result.stdout))


def test_w02_arithmetic() -> None:
    from w02_arithmetic import analytic_checksum

    for n in (0, 1, 1000, 12345):
        result = subprocess.run(
            [PY, str(HERE / "w02_arithmetic.py"), str(n)],
            capture_output=True, text=True, timeout=10,
        )
        expected = analytic_checksum(n)
        actual = int(result.stdout.strip())
        check(f"w02_analytic_checksum_n{n}", actual == expected, f"expected {expected}, got {actual}")


def test_w17_logvolume() -> None:
    from w17_logvolume import make_bytes

    for mode in ("burst", "chunked"):
        result = subprocess.run(
            [PY, str(HERE / "w17_logvolume.py"), "1000", "500", mode, "64"],
            capture_output=True, timeout=10,
        )
        check(f"w17_{mode}_stdout_byte_count_exact", len(result.stdout) == 1000, str(len(result.stdout)))
        check(f"w17_{mode}_stderr_byte_count_exact", len(result.stderr) == 500, str(len(result.stderr)))
        check(f"w17_{mode}_stdout_content_exact", result.stdout == make_bytes(1000), "content mismatch, not just length")
        check(f"w17_{mode}_stderr_content_exact", result.stderr == make_bytes(500), "content mismatch, not just length")


def test_w18_wait() -> None:
    requested = 0.3
    start = time.monotonic()
    result = subprocess.run(
        [PY, str(HERE / "w18_wait.py"), str(requested)],
        capture_output=True, text=True, timeout=10,
    )
    elapsed = time.monotonic() - start
    check("w18_exit_zero", result.returncode == 0, str(result.returncode))
    check("w18_reports_requested_interval", result.stdout.strip() == f"waited={requested}", repr(result.stdout))
    check(
        "w18_actually_waited_at_least_requested",
        elapsed >= requested,
        f"elapsed {elapsed:.3f}s < requested {requested}s",
    )


def test_w19_memlifetime() -> None:
    alloc_mb = 4
    retain_s = 0.2
    result = subprocess.run(
        [PY, str(HERE / "w19_memlifetime.py"), str(alloc_mb), str(retain_s)],
        capture_output=True, text=True, timeout=10,
    )
    check("w19_exit_zero", result.returncode == 0, str(result.returncode))
    lines = result.stdout.strip().splitlines()
    check(
        "w19_lifecycle_output_exact",
        lines == [f"allocated_mb={alloc_mb}", f"retained_seconds={retain_s}", "released=true"],
        str(lines),
    )


def main() -> int:
    test_w00_noop()
    test_w02_arithmetic()
    test_w17_logvolume()
    test_w18_wait()
    test_w19_memlifetime()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print("All harness-control workloads (W00, W02, W17, W18, W19) behave exactly as specified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
