#!/usr/bin/env python3
"""BP07: the pilot variance and cost report, generated from
pilot_results.tsv (2 sessions x 5 blocks per cell). Per docs/
benchmarks/performance-protocol.md: "Keep pilot observations out of
confirmatory estimates" -- this report is descriptive (variance, cost,
behavior-check pass rate) and demonstrates the analysis pipeline
(analyze.py) against REAL data for the first time, but does NOT treat
its own log-ratio/CI output as a confirmatory finding. With only 2
pilot sessions (df=1), any Student-t interval is necessarily very
wide -- that is expected and correctly signals "more sessions needed,"
not a pipeline defect.

Run: python3 pilot_report.py
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze import SessionBlockTime, paired_log_ratio_overhead  # noqa: E402

RESULTS_PATH = Path(__file__).parent / "pilot_results.tsv"


def load_rows() -> list[dict]:
    with RESULTS_PATH.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main() -> int:
    rows = load_rows()
    if not rows:
        print("no pilot rows found -- has run_pilot.py finished?", file=sys.stderr)
        return 1

    by_cell_condition: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    behavior_by_cell: dict[tuple[str, str], list[bool]] = defaultdict(list)
    artifact_by_cell: dict[tuple[str, str], list[bool]] = defaultdict(list)
    # (candidate, workload, session, block, condition) -> time, for pairing
    by_cell_session_block: dict[tuple[str, str], dict[tuple[int, int, str], float]] = defaultdict(dict)
    # Same shape, but for the in-process work_time_seconds field (W03/W05/W11
    # only -- W01 has no measurable useful work per its own catalog rule).
    # Corrected 2026-09-20 after a review found this report computed EVERY
    # ratio/CI from process_interval_seconds only, despite this file's own
    # module docstring and pilot/performance/README.md claiming the ratios
    # were "work-time-based" -- they were not; process time includes the
    # ~3.5-5.6s fixed startup floor that dwarfs the actual per-work overhead
    # this study is supposed to measure, understating every real effect
    # (e.g. gd-tools w03's true work-time C/B0 ratio is ~12x, not the ~5.3x
    # process-time ratio the old report-only numbers showed).
    by_cell_condition_work: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    by_cell_session_block_work: dict[tuple[str, str], dict[tuple[int, int, str], float]] = defaultdict(dict)
    timestamps: list[float] = []

    excluded_count = 0
    for row in rows:
        candidate, workload, condition = row["candidate"], row["workload"], row["condition"]
        t = float(row["process_interval_seconds"])
        work_t_raw = row.get("work_time_seconds", "")
        work_t = float(work_t_raw) if work_t_raw not in (None, "", "None") else None
        ok = row["behavior_ok"] == "True"
        timed_out = row.get("timed_out") == "True"
        behavior_by_cell[(candidate, workload)].append(ok)
        if row.get("coverage_artifact_ok") not in (None, "", "None"):
            artifact_by_cell[(candidate, workload)].append(row["coverage_artifact_ok"] == "True")
        timestamps.append(float(row["timestamp"]))
        # Per docs/benchmarks/performance-protocol.md: a failed or timed-out
        # attempt is RETAINED as a row (see run_pilot.py) but must never be
        # averaged into success-condition statistics or used as a paired
        # log-ratio observation -- a truncated/failed duration is not a real
        # completion time. Caught by an independent review of the first
        # corrected pilot run (this run had zero failures, so the bug was
        # latent, not yet manifested).
        if not ok or timed_out:
            excluded_count += 1
            continue
        by_cell_condition[(candidate, workload, condition)].append(t)
        session, block = int(row["session"]), int(row["block"])
        by_cell_session_block[(candidate, workload)][(session, block, condition)] = t
        if work_t is not None:
            by_cell_condition_work[(candidate, workload, condition)].append(work_t)
            by_cell_session_block_work[(candidate, workload)][(session, block, condition)] = work_t

    if excluded_count:
        print(f"NOTE: {excluded_count} row(s) with behavior_ok=False or timed_out=True "
              f"were retained in pilot_results.tsv but EXCLUDED from all statistics below.")
        print()

    print("=" * 90)
    print("DESCRIPTIVE STATISTICS per (candidate, workload, condition)")
    print("=" * 90)
    total_wall_seconds = 0.0
    for (candidate, workload, condition), times in sorted(by_cell_condition.items()):
        total_wall_seconds += sum(times)
        mean = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        cv = (stdev / mean * 100) if mean > 0 else 0.0
        print(
            f"{candidate:15s} {workload:4s} {condition:3s}  n={len(times):3d}  "
            f"mean={mean:.3f}s  stdev={stdev:.3f}s  CV={cv:5.1f}%  "
            f"min={min(times):.3f}s  max={max(times):.3f}s"
        )

    print()
    print("=" * 90)
    print("WORK-TIME DESCRIPTIVE STATISTICS per (candidate, workload, condition) -- W03/W05/W11 only")
    print("=" * 90)
    for (candidate, workload, condition), times in sorted(by_cell_condition_work.items()):
        mean = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        cv = (stdev / mean * 100) if mean > 0 else 0.0
        print(
            f"{candidate:15s} {workload:4s} {condition:3s}  n={len(times):3d}  "
            f"mean={mean:.3f}s  stdev={stdev:.3f}s  CV={cv:5.1f}%  "
            f"min={min(times):.3f}s  max={max(times):.3f}s"
        )

    print()
    print("=" * 90)
    print("BEHAVIOR CHECK PASS RATE per (candidate, workload)")
    print("=" * 90)
    any_failures = False
    for (candidate, workload), oks in sorted(behavior_by_cell.items()):
        n_ok = sum(oks)
        n_total = len(oks)
        if n_ok != n_total:
            any_failures = True
        print(f"{candidate:15s} {workload:4s}  {n_ok}/{n_total} passed")
    if not any_failures:
        print("All cells: 100% behavior-check pass rate across the pilot.")

    print()
    print("=" * 90)
    print("COVERAGE ARTIFACT PRESENCE (condition C only -- did the collector actually produce output)")
    print("=" * 90)
    if artifact_by_cell:
        any_artifact_failures = False
        for (candidate, workload), oks in sorted(artifact_by_cell.items()):
            n_ok = sum(oks)
            n_total = len(oks)
            if n_ok != n_total:
                any_artifact_failures = True
            print(f"{candidate:15s} {workload:4s}  {n_ok}/{n_total} produced a real coverage artifact")
        if not any_artifact_failures:
            print("All C-condition runs: coverage artifact confirmed present in every case.")
    else:
        print("No coverage_artifact_ok data in this file (older-format pilot_results.tsv).")

    def print_log_ratio_section(title: str, session_block_data: dict, keys) -> None:
        print()
        print("=" * 90)
        print(title)
        print("=" * 90)
        for candidate, workload in sorted(keys):
            cell_data = session_block_data.get((candidate, workload), {})
            if not cell_data:
                print(f"{candidate:15s} {workload:4s}  (no data)")
                continue
            sessions = sorted({s for (s, b, c) in cell_data})
            blocks = sorted({b for (s, b, c) in cell_data})
            conditions_seen = sorted({c for (s, b, c) in cell_data})
            pairs = [("C", "B0"), ("B1", "B0"), ("C", "B1")]
            for numerator, denominator in pairs:
                if numerator not in conditions_seen or denominator not in conditions_seen:
                    continue
                records = []
                for s in sessions:
                    for b in blocks:
                        ta = cell_data.get((s, b, denominator))
                        tb = cell_data.get((s, b, numerator))
                        if ta is not None and tb is not None:
                            records.append(SessionBlockTime(session=s, block=b, time_a=ta, time_b=tb))
                if len(records) < 4:
                    continue
                try:
                    est = paired_log_ratio_overhead(records)
                    mean_a = statistics.mean(r.time_a for r in records)  # denominator condition
                    mean_b = statistics.mean(r.time_b for r in records)  # numerator condition
                    print(
                        f"{candidate:15s} {workload:4s} {numerator}/{denominator}: "
                        f"R={est.r:.4f} overhead={est.overhead_percent:+.2f}% "
                        f"(absolute delta ~{mean_b - mean_a:+.3f}s, {denominator} mean {mean_a:.3f}s) "
                        f"95% CI=[{est.ci_low:.4f}, {est.ci_high:.4f}] (n_sessions={est.n_sessions}, df={est.df} -- WIDE, exploratory only)"
                    )
                except ValueError as e:
                    print(f"{candidate:15s} {workload:4s} {numerator}/{denominator}: could not estimate ({e})")

    print_log_ratio_section(
        "EXPLORATORY log-ratio estimates, PROCESS TIME (includes fixed startup floor -- "
        "NOT confirmatory, 2 sessions, df=1)",
        by_cell_session_block, behavior_by_cell.keys(),
    )
    print()
    print("Process-time ratios above are DILUTED by each run's fixed process/startup "
          "floor (~3.5-5.6s for gd-tools, ~1.8-3.8s for Nano Coverage) and are NOT the "
          "study's primary metric -- see the WORK-TIME section below for the number that "
          "actually estimates per-work coverage overhead, per workload-catalog.tsv's own "
          "calibration_rule ('1-5 seconds of B0 work', not process time).")

    print_log_ratio_section(
        "EXPLORATORY log-ratio estimates, WORK TIME ONLY (in-process fixed-work span, "
        "excludes startup floor -- the study's primary metric; NOT confirmatory, 2 "
        "sessions, df=1)",
        by_cell_session_block_work, [(c, w) for (c, w) in behavior_by_cell.keys() if w != "w01"],
    )
    print()
    print("Percentage overhead is NOT comparable across candidates even in work-time "
          "terms if the workload's own execution speed differs meaningfully between "
          "candidates' runners -- compare absolute work-time deltas across candidates "
          "when in doubt. See README.md's 'known confounds' section.")

    print()
    print("=" * 90)
    print("COST EXTRAPOLATION")
    print("=" * 90)
    pilot_runs = len(rows)
    # Two numbers, deliberately both shown: summed TIMED intervals (the
    # thing analyze.py actually uses) vs. the REAL wall-clock span this
    # script's own process observed (timestamps min-to-max). The first
    # excludes each run's untimed scratch-rebuild + --import cost; the
    # second includes it. A first version of this report used only the
    # timed-interval sum for its main-study estimate, understating real
    # machine time needed by roughly 2x (an independent review measured
    # the gap directly on the first, since-retracted pilot run).
    wall_clock_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else total_wall_seconds
    print(f"Pilot: {pilot_runs} runs")
    print(f"  Sum of TIMED intervals only: {total_wall_seconds:.1f}s ({total_wall_seconds/60:.1f} min)")
    print(f"  REAL wall-clock span (includes untimed setup/import per run): {wall_clock_span:.1f}s ({wall_clock_span/60:.1f} min)")
    mean_per_run_wall = wall_clock_span / pilot_runs if pilot_runs else 0
    # Main study: 10 sessions x 6 blocks per cell (vs. pilot's 2x5), same 8 cells.
    main_study_runs_per_cell_ratio = (10 * 6) / (2 * 5)
    estimated_main_runs = pilot_runs * main_study_runs_per_cell_ratio
    estimated_main_wall_seconds = wall_clock_span * main_study_runs_per_cell_ratio
    print(f"Mean wall-clock per run (realistic budgeting unit): {mean_per_run_wall:.2f}s")
    print(
        f"Extrapolated main study (10 sessions x 6 blocks per cell, same 8 cells), "
        f"using REAL wall-clock per run: "
        f"~{estimated_main_runs:.0f} runs, ~{estimated_main_wall_seconds/60:.0f} min "
        f"(~{estimated_main_wall_seconds/3600:.1f} hours) of machine time"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
