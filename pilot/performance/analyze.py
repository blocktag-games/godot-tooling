#!/usr/bin/env python3
"""BP09: the performance analysis pipeline, implementing
docs/benchmarks/performance-protocol.md's Statistical Analysis section
exactly:

    d[s,b] = ln(time_C[s,b] / time_B0[s,b])
    m[s]   = mean of d[s,b] within session s
    R      = exp(mean of m[s] across sessions)
    overhead_percent = 100 * (R - 1)

R is the geometric mean paired ratio with equal session weighting --
NOT the ratio of arithmetic mean durations. The confidence interval is
a two-sided Student-t interval on the SESSION MEANS m[s] (not on the
raw per-block ratios), transformed back with exp, per the protocol's
explicit requirement.

This module is generic over which two conditions are being compared
(time_a is always the denominator, time_b the numerator) -- call it
once for C/B0, once for B1/B0, once for C/B1, per the protocol's
"Report C/B0, B1/B0, and C/B1 where available" instruction.

Requires scipy (for the Student-t critical value) -- the only
scipy/numpy dependency anywhere in this project; not needed by the
correctness harness or any coverage-comparison code, only here.

Run pilot/performance/validate_analyze.py before trusting this module
against real timing data -- it validates the whole pipeline (including
the CI's actual coverage rate) against synthetic data with a known,
planted ratio, per BP09's "validated analysis on synthetic known data"
completion requirement.
"""
from __future__ import annotations

import csv
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from scipy import stats as scipy_stats


@dataclass
class SessionBlockTime:
    session: int
    block: int
    time_a: float  # denominator condition (e.g. B0)
    time_b: float  # numerator condition (e.g. C)


@dataclass
class OverheadEstimate:
    r: float                        # geometric mean paired ratio (b/a)
    overhead_percent: float         # 100 * (r - 1)
    ci_low: float
    ci_high: float
    confidence: float
    n_sessions: int
    df: int
    session_means: dict[int, float]  # session -> mean log-ratio m[s]


def paired_log_ratio_overhead(
    records: list[SessionBlockTime], confidence: float = 0.95
) -> OverheadEstimate:
    if not records:
        raise ValueError("no records provided")

    by_session: dict[int, list[float]] = {}
    for rec in records:
        if rec.time_a <= 0 or rec.time_b <= 0:
            raise ValueError(
                f"non-positive elapsed time in session {rec.session} block "
                f"{rec.block}: time_a={rec.time_a} time_b={rec.time_b} -- "
                f"per the protocol's invalidity rules, a non-positive elapsed "
                f"time is not a real observation to analyze"
            )
        d = math.log(rec.time_b / rec.time_a)
        by_session.setdefault(rec.session, []).append(d)

    session_means = {s: statistics.mean(ds) for s, ds in by_session.items()}
    n = len(session_means)
    if n < 2:
        raise ValueError(
            f"need at least 2 sessions for a Student-t interval on session "
            f"means, got {n}"
        )

    m_values = list(session_means.values())
    grand_mean = statistics.mean(m_values)
    sd = statistics.stdev(m_values)  # sample stdev, ddof=1, matches protocol
    se = sd / math.sqrt(n)
    df = n - 1
    t_crit = scipy_stats.t.ppf(1 - (1 - confidence) / 2, df)

    r = math.exp(grand_mean)
    ci_low = math.exp(grand_mean - t_crit * se)
    ci_high = math.exp(grand_mean + t_crit * se)

    return OverheadEstimate(
        r=r,
        overhead_percent=100.0 * (r - 1.0),
        ci_low=ci_low,
        ci_high=ci_high,
        confidence=confidence,
        n_sessions=n,
        df=df,
        session_means=session_means,
    )


def load_session_block_tsv(path: Path) -> list[SessionBlockTime]:
    """Reads a TSV with header columns: session, block, time_a, time_b."""
    records = []
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            records.append(
                SessionBlockTime(
                    session=int(row["session"]),
                    block=int(row["block"]),
                    time_a=float(row["time_a"]),
                    time_b=float(row["time_b"]),
                )
            )
    return records


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: analyze.py <session_block_times.tsv>", file=sys.stderr)
        return 2
    records = load_session_block_tsv(Path(sys.argv[1]))
    est = paired_log_ratio_overhead(records)
    print(f"R (geometric mean paired ratio, time_b/time_a) = {est.r:.4f}")
    print(f"overhead = {est.overhead_percent:+.2f}%")
    print(f"{int(est.confidence * 100)}% CI on R: [{est.ci_low:.4f}, {est.ci_high:.4f}]")
    print(f"sessions = {est.n_sessions}, df = {est.df}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
