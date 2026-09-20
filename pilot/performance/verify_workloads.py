#!/usr/bin/env python3
"""BP07 preparation: correctness verification for the four primary
workloads (W01, W03, W05, W11), against the raw pinned Godot engine --
NO coverage tool involved at all (not gd-tools, not Nano Coverage, not
GUT, not GdUnit4). This is a functional correctness check of the
fixed-work DEFINITIONS themselves, run exactly once per workload, the
same category as verifying any correctness fixture in this project
(build, run once, confirm it's not broken). It is explicitly NOT a
timed pilot or calibration run, and no timing is recorded here.

For W03 and W11, an independent Python re-implementation of the same
deterministic formula provides the expected result -- the same pattern
established for W02's analytic checksum -- so the check does not trust
the GDScript's own logic to grade itself.

Run: python3 verify_workloads.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def run_driver(driver: str, args: list[str]) -> dict:
    result = subprocess.run(
        [str(GODOT_BIN), "--headless", "--path", str(HERE), "--script", f"drivers/{driver}", "--", *args],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{driver} exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}")
    # The driver's JSON is the last non-empty stdout line (Godot may
    # print engine banner lines before it).
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        raise RuntimeError(f"{driver} produced no stdout\nstderr={result.stderr}")
    return json.loads(lines[-1])


def w03_reference(n: int) -> dict:
    counts = {"low": 0, "mid_low": 0, "mid_high": 0, "high": 0, "very_high": 0}
    for i in range(n):
        v = (i * 2654435761) % 1000
        if v < 100:
            counts["low"] += 1
        elif v < 400:
            counts["mid_low"] += 1
        elif v < 700:
            counts["mid_high"] += 1
        elif v < 950:
            counts["high"] += 1
        else:
            counts["very_high"] += 1
    return counts


def w11_reference(n_steps: int, seed_value: int) -> dict:
    score = 0
    health = 100
    log_length = 0
    milestones_seen: list[int] = []
    for step in range(n_steps):
        v = (step * 2654435761 + seed_value) % 100
        if v < 10:
            delta = -5
        elif v < 60:
            delta = 1
        else:
            delta = 3
        score += delta
        if v < 10:
            health -= 1
        log_length += 1
        if score > 0 and score % 50 == 0 and score not in milestones_seen:
            milestones_seen.append(score)
    return {"score": score, "health": health, "milestones": milestones_seen, "log_length": log_length}


def test_w01() -> None:
    result = run_driver("w01_driver.gd", [])
    check("w01_sentinel_result", result["sentinel_result"] == 42, str(result))


def test_w03() -> None:
    for n in (0, 1, 100, 10000):
        result = run_driver("w03_driver.gd", [str(n)])
        expected = w03_reference(n)
        check(f"w03_counts_match_reference_n{n}", result == expected, f"expected {expected}, got {result}")


def test_w05() -> None:
    n_listeners, n_direct, n_deferred = 10, 7, 5
    result = run_driver("w05_driver.gd", [str(n_listeners), str(n_direct), str(n_deferred)])
    expected_total = n_listeners * (n_direct + n_deferred)
    check(
        "w05_total_delivered_matches_expected",
        result["total_delivered"] == expected_total,
        f"expected {expected_total}, got {result}",
    )


def test_w11() -> None:
    for n_steps, seed_value in [(0, 1), (1, 1), (200, 12345), (500, 999)]:
        result = run_driver("w11_driver.gd", [str(n_steps), str(seed_value)])
        expected = w11_reference(n_steps, seed_value)
        actual = {k: result[k] for k in ("score", "health", "milestones", "log_length")}
        check(
            f"w11_final_state_matches_reference_n{n_steps}_seed{seed_value}",
            actual == expected,
            f"expected {expected}, got {actual}",
        )


def main() -> int:
    test_w01()
    test_w03()
    test_w05()
    test_w11()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "All four primary workloads (W01, W03, W05, W11) produce correct, "
        "independently-verified results against the raw pinned engine -- no "
        "coverage tool involved, no timing recorded. Fixed-work definitions "
        "are correct; calibrating their sizes against B0 timing (the pilot "
        "itself) remains unexecuted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
