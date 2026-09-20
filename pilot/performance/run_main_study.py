#!/usr/bin/env python3
"""BP10: the controlled main study runner. 10 sessions x 6 blocks per
(candidate, workload) cell, per docs/benchmarks/performance-protocol.md's
"Pilot, freeze, and repeat" item 3's frozen default -- NOT the BP07
pilot's 2x5, and NOT the pilot's simpler per-block shuffle (see
main_study_schedule.py's module docstring).

Differences from run_pilot.py, all required by BP09's freeze before
this script may be used for real data collection:

1. Real balancing: three_condition_block_orders/two_condition_block_orders
   give exact per-position condition balance, not merely a random
   shuffle. A separate cross_cell_seed shuffles which cell runs when
   within a session, independent of each cell's own block order.
2. Per-condition cache isolation: every run passes isolate_user_dir=True
   to run_condition(), giving each (candidate, workload, condition) its
   own OS-level Godot user-data directory (closing the BP07 pilot's
   documented, harmless-there-but-not-here shared-cache gap).
3. A measured idle-CPU quiescence gate (quiescence.py) runs before
   EVERY session, not assumed from a rest interval. This is a hard
   gate: it raises and stops the whole study rather than proceeding on
   an unverified assumption of a quiet machine.
4. Environment capture (capture_environment.py) is recorded once per
   session, not just once for the whole study, so session-to-session
   drift (thermal or otherwise) has a chance of being visible in the
   record even though this machine has no direct thermal telemetry.

Unattended, multi-hour run: writes each row to disk immediately
(flushed), same as run_pilot.py, so a crash or an aborted quiescence
gate loses at most the in-flight session, not the whole study.

Run: python3 run_main_study.py
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from candidates import GD_TOOLS, NANO_COVERAGE, CandidateConfig  # noqa: E402
from run_condition import run_condition  # noqa: E402
from main_study_schedule import (  # noqa: E402
    block_order_seed, cross_cell_seed, cross_cell_order,
    three_condition_block_orders, two_condition_block_orders,
)
from quiescence import wait_for_quiescence  # noqa: E402
from capture_environment import capture as capture_environment  # noqa: E402

WORKLOADS = ["w01", "w03", "w05", "w11"]
N_SESSIONS = 10
N_BLOCKS = 6
QUIESCENCE_BUSY_THRESHOLD_PCT = 5.0
QUIESCENCE_WINDOW_S = 60.0

RESULTS_PATH = Path(__file__).parent / "main_study_results.tsv"
SESSION_LOG_PATH = Path(__file__).parent / "main_study_sessions.jsonl"
FIELDNAMES = [
    "candidate", "workload", "session", "block_order_seed", "cross_cell_seed", "block",
    "condition", "order_in_block", "process_interval_seconds", "work_time_seconds",
    "exit_code", "behavior_ok", "coverage_artifact_ok", "timed_out",
    "import_exit_code", "import_timed_out", "timestamp",
]

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

# Every eligible (candidate, workload) primary cell, per
# docs/benchmarks/performance-eligible-cells.tsv.
CELLS: list[tuple[CandidateConfig, str]] = [
    (candidate, workload)
    for candidate in (GD_TOOLS, NANO_COVERAGE)
    for workload in WORKLOADS
]


def run_one_cell_one_block(
    candidate: CandidateConfig, workload: str, session: int, b_seed: int,
    block: int, order: tuple, writer: csv.DictWriter, fh, c_seed: int,
) -> None:
    for idx, condition in enumerate(order):
        result = run_condition(
            candidate, workload, condition,
            extra_env=WORKLOAD_EXTRA_ENV.get(workload, {}),
            scratch_label=f"main-study-{candidate.name}-{workload}",
            isolate_user_dir=True,
        )
        row = {
            "candidate": candidate.name,
            "workload": workload,
            "session": session,
            "block_order_seed": b_seed,
            "cross_cell_seed": c_seed,
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


def run_session(session: int, writer: csv.DictWriter, fh, session_log) -> None:
    print(f"\n{'=' * 20} SESSION {session} {'=' * 20}")
    print(f"Waiting for machine quiescence (busy% <= {QUIESCENCE_BUSY_THRESHOLD_PCT}% "
          f"over a {QUIESCENCE_WINDOW_S}s window) before this session starts...")
    quiescence_record = wait_for_quiescence(
        busy_threshold_pct=QUIESCENCE_BUSY_THRESHOLD_PCT, window_s=QUIESCENCE_WINDOW_S,
    )
    print(f"Quiescence confirmed: {quiescence_record}")

    environment_record = capture_environment()

    c_seed = cross_cell_seed(session)
    ordered_cells = cross_cell_order(c_seed, [(c.name, w) for c, w in CELLS])
    cells_by_name = {c.name: c for c, _ in CELLS}

    session_log.write(json.dumps({
        "session": session,
        "cross_cell_seed": c_seed,
        "cross_cell_order": ordered_cells,
        "quiescence": quiescence_record,
        "environment": environment_record,
        "started_at": time.time(),
    }) + "\n")
    session_log.flush()

    # Interpretation of "shuffle cell order within sessions" (the frozen
    # protocol text does not disambiguate this -- documented here rather
    # than left implicit): cells are INTERLEAVED across the session in
    # one fixed shuffled order, one block from each cell per round, not
    # run as 6 contiguous blocks per cell before moving to the next.
    # Interleaving spreads any within-session time/thermal drift evenly
    # across every cell; running cells as separate contiguous chunks
    # would concentrate that drift on whichever cell happens to run
    # last. This is a stronger, not weaker, reading of the requirement.
    for block in range(N_BLOCKS):
        for candidate_name, workload in ordered_cells:
            candidate = cells_by_name[candidate_name]
            b_seed = block_order_seed(candidate.name, workload, session)
            if candidate.has_b1:
                orders = three_condition_block_orders(b_seed, N_BLOCKS)
            else:
                orders = two_condition_block_orders(b_seed, N_BLOCKS)
            run_one_cell_one_block(candidate, workload, session, b_seed, block, orders[block], writer, fh, c_seed)


def main() -> int:
    with RESULTS_PATH.open("w", newline="") as f, SESSION_LOG_PATH.open("w") as session_log:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        f.flush()
        for session in range(N_SESSIONS):
            try:
                run_session(session, writer, f, session_log)
            except RuntimeError as e:
                # The quiescence gate's own abort (see quiescence.py) --
                # every row and session log entry written so far is
                # already flushed to disk and remains valid; only the
                # NOT-yet-started remainder of the study is lost. Do not
                # silently continue on an unverified assumption of quiet.
                print(f"\nABORTED at session {session}: {e}", file=sys.stderr)
                print(f"Partial results retained in {RESULTS_PATH} and {SESSION_LOG_PATH} "
                      f"({session} of {N_SESSIONS} sessions completed).", file=sys.stderr)
                return 1
    print(f"\nWrote {RESULTS_PATH} and {SESSION_LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
