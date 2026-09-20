#!/usr/bin/env python3
"""BP07: the pilot itself. 2 sessions x 5 blocks per (candidate,
workload) cell, per docs/benchmarks/performance-protocol.md's "Pilot,
freeze, and repeat" section. Each block runs every condition
applicable to that candidate (B0/B1/C for gd-tools, B0/C for Nano
Coverage -- never synthesizing a B1 Nano Coverage doesn't have) in a
RECORDED random order, one fresh process per condition.

Writes each row to disk immediately (flushed) as it completes -- not
batched at the end -- so a crash partway through this ~30-60 minute
sweep loses at most the one in-flight row, not the whole run.

Behavior-check failures are RECORDED as an outcome (behavior_ok=False)
via run_condition()'s positive-evidence check (did the workload's own
assertion actually pass -- NOT just a zero exit code, see run_condition.py's
module docstring for why that distinction matters), never raised as an
exception that kills the sweep -- per the protocol's explicit rule
that timeouts/failures remain in the data, not silently dropped.
Timeouts are handled the same way, via pilot/harness/runner.py's
process-group-safe run().

Session order-randomization seeds are derived deterministically from
(candidate, workload, session) via sha256, NOT Python's built-in
hash() (which is randomized per-process by default and would make
"the recorded seed" meaningless on a rerun) -- and are written into
the output alongside every row, so the exact schedule is reproducible
and auditable independent of this script's own source.

Run: python3 run_pilot.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS, NANO_COVERAGE, CandidateConfig  # noqa: E402
from run_condition import run_condition  # noqa: E402

WORKLOADS = ["w01", "w03", "w05", "w11"]
N_SESSIONS = 2
N_BLOCKS = 5

# Loaded from calibration_result.json rather than relying on the
# GDScript test wrappers' own DEFAULT_* fallback constants (or the
# separate Python-side mirror of them in run_condition.py) matching --
# a real bug during recalibration (this file's own git history):
# calibrate.py froze new sizes into the GDScript files, but the
# Python-side mirror constants used to build the independent expected-
# value oracle were NOT updated in the same pass, so the pilot would
# have silently checked every w03/w11 run against the WRONG expected
# result. Passing the calibrated size explicitly here, sourced from the
# same JSON file calibrate.py writes, means the actual pilot run never
# depends on the GDScript defaults and the oracle computation agreeing
# by separate manual edits -- there is exactly one frozen source of
# truth for what size each real pilot run uses.
_CALIBRATION = json.loads((Path(__file__).parent / "calibration_result.json").read_text())
WORKLOAD_EXTRA_ENV: dict[str, dict[str, str]] = {
    "w01": {},
    "w03": {"PERF_W03_N": str(_CALIBRATION["w03"]["n"])},
    "w05": {
        "PERF_W05_N_LISTENERS": str(_CALIBRATION["w05"]["n_listeners"]),
        "PERF_W05_N_DIRECT": str(_CALIBRATION["w05"]["n_direct"]),
        "PERF_W05_N_DEFERRED": str(_CALIBRATION["w05"]["n_deferred"]),
    },
    "w11": {
        "PERF_W11_N_STEPS": str(_CALIBRATION["w11"]["n_steps"]),
        "PERF_W11_SEED": str(_CALIBRATION["w11"]["seed"]),
    },
}

OUT_PATH = Path(__file__).parent / "pilot_results.tsv"
FIELDNAMES = [
    "candidate", "workload", "session", "session_seed", "block", "condition",
    "order_in_block", "process_interval_seconds", "work_time_seconds", "exit_code", "behavior_ok",
    "coverage_artifact_ok", "timed_out", "import_exit_code", "import_timed_out", "timestamp",
]

# NOTE on scope (2026-09-20): the protocol's "balance AB/BA ordering"
# and "shuffle cell order within sessions using a separate recorded
# seed" (performance-protocol.md's Pilot/freeze items 3-4) apply to
# the FROZEN MAIN STUDY schedule ("for each primary cell, initially
# budget ten measurement sessions..."), not to this 2x5 PILOT (item 1's
# own job is only "randomized blocks" to establish valid behavior and
# variance). This script deliberately does NOT implement cross-cell
# shuffling or AB/BA balance for the pilot -- matching this project's
# established scope decision that BP10-level rigor is not a BP07-09
# requirement. BP10's own schedule design will need real AB/BA
# balancing and cross-cell ordering; this pilot's per-block shuffle
# (recorded, reproducible via session_seed) is sufficient for its own
# stated purpose.


def session_seed(candidate_name: str, workload: str, session: int) -> int:
    key = f"{candidate_name}:{workload}:{session}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")


def run_cell(candidate: CandidateConfig, workload: str, writer: csv.DictWriter, fh) -> None:
    conditions = list(candidate.project_godot_fragments.keys())
    for session in range(N_SESSIONS):
        seed = session_seed(candidate.name, workload, session)
        rng = random.Random(seed)
        for block in range(N_BLOCKS):
            order = conditions[:]
            rng.shuffle(order)
            for idx, condition in enumerate(order):
                result = run_condition(
                    candidate, workload, condition,
                    extra_env=WORKLOAD_EXTRA_ENV.get(workload, {}),
                    scratch_label=f"pilot-{candidate.name}-{workload}",
                )
                row = {
                    "candidate": candidate.name,
                    "workload": workload,
                    "session": session,
                    "session_seed": seed,
                    "block": block,
                    "condition": condition,
                    "order_in_block": idx,
                    "process_interval_seconds": f"{result.process_interval_seconds:.4f}",
                    "work_time_seconds": f"{result.work_time_seconds:.6f}" if result.work_time_seconds is not None else "",
                    "exit_code": result.exit_code,
                    "behavior_ok": result.behavior_ok,
                    "coverage_artifact_ok": result.coverage_artifact_ok,
                    "timed_out": result.timed_out,
                    "import_exit_code": result.import_exit_code,
                    "import_timed_out": result.import_timed_out,
                    "timestamp": f"{time.time():.3f}",
                }
                writer.writerow(row)
                fh.flush()
                marker = "OK" if result.behavior_ok else "FAIL"
                artifact_note = f" artifact_ok={result.coverage_artifact_ok}" if result.coverage_artifact_ok is not None else ""
                print(
                    f"{marker} {candidate.name}/{workload} session={session} block={block} "
                    f"order={idx} condition={condition}: {result.process_interval_seconds:.3f}s{artifact_note}"
                )
                if not result.behavior_ok:
                    print(f"     behavior check failed -- stdout tail: {result.stdout[-300:]!r}")
                if condition == "C" and result.coverage_artifact_ok is False:
                    print(f"     WARNING: condition C produced no coverage artifact -- stdout tail: {result.stdout[-300:]!r}")


def main() -> int:
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        f.flush()
        for candidate in (GD_TOOLS, NANO_COVERAGE):
            for workload in WORKLOADS:
                print(f"\n=== {candidate.name} / {workload} ===")
                run_cell(candidate, workload, writer, f)
    print(f"\nWrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
