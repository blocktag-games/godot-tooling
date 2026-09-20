#!/usr/bin/env python3
"""BP09: validate the analysis pipeline (analyze.py) against synthetic
data with a KNOWN, planted ratio -- this project's completion evidence
requirement for BP09 is "validated analysis on synthetic known data",
and this file is that validation, run BEFORE the pipeline is ever
pointed at real BP10 timing data.

Two checks, both against a log-normal generative model matching the
protocol's own assumption (session means m[s] approximately normal on
the log scale):

1. A single deterministic draw (fixed seed) with a known planted ratio:
   the point estimate must land close to the true ratio, and the 95%
   CI must actually bracket it.
2. A Monte Carlo coverage check: repeat the draw-and-estimate procedure
   many times under the same known generative model and confirm the
   95% CI's ACTUAL coverage rate is close to 95% -- this is the
   standard way to validate that a confidence-interval procedure is
   not mis-specified (wrong transform, off-by-one degrees of freedom,
   z instead of t, etc.), which a single lucky draw cannot catch.

Run: python3 validate_analyze.py
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from analyze import SessionBlockTime, paired_log_ratio_overhead  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def generate_synthetic(
    r_true: float,
    n_sessions: int,
    n_blocks: int,
    session_sd: float,
    block_sd: float,
    base_time: float,
    seed: int,
) -> list[SessionBlockTime]:
    """Log-normal generative model: each session has its own mean
    log-ratio (log(r_true) + session-level noise), and each block within
    a session adds further block-level noise on top of that -- matching
    the protocol's two-level structure (blocks nested in sessions) that
    the analysis pipeline's session-mean-then-across-session procedure
    is specifically designed for.
    """
    rng = random.Random(seed)
    log_r_true = math.log(r_true)
    records = []
    for s in range(n_sessions):
        session_log_r = log_r_true + rng.gauss(0, session_sd)
        for b in range(n_blocks):
            d = session_log_r + rng.gauss(0, block_sd)
            time_a = base_time * math.exp(rng.gauss(0, 0.05))
            time_b = time_a * math.exp(d)
            records.append(SessionBlockTime(session=s, block=b, time_a=time_a, time_b=time_b))
    return records


def test_deterministic_recovery_of_known_overhead() -> None:
    r_true = 1.35
    records = generate_synthetic(
        r_true=r_true, n_sessions=10, n_blocks=6,
        session_sd=0.03, block_sd=0.05, base_time=1.0, seed=42,
    )
    est = paired_log_ratio_overhead(records)
    check(
        "point_estimate_close_to_planted_ratio",
        abs(est.r - r_true) / r_true < 0.05,
        f"planted R={r_true}, estimated R={est.r:.4f} (>5% relative error)",
    )
    check(
        "ci_brackets_planted_ratio",
        est.ci_low <= r_true <= est.ci_high,
        f"planted R={r_true} not in [{est.ci_low:.4f}, {est.ci_high:.4f}]",
    )
    check("n_sessions_correct", est.n_sessions == 10, str(est.n_sessions))
    check("df_correct", est.df == 9, str(est.df))


def test_deterministic_recovery_of_zero_overhead() -> None:
    """A second known value (no overhead at all, R=1.0) -- a pipeline
    bug that only manifests away from R=1.35 (e.g. an incorrect log-
    base, or a sign error that only matters when R != 1) would not be
    caught by the first test alone.
    """
    r_true = 1.0
    records = generate_synthetic(
        r_true=r_true, n_sessions=10, n_blocks=6,
        session_sd=0.03, block_sd=0.05, base_time=2.5, seed=99,
    )
    est = paired_log_ratio_overhead(records)
    check(
        "zero_overhead_point_estimate_close_to_one",
        abs(est.r - 1.0) < 0.05,
        f"expected R close to 1.0, got {est.r:.4f}",
    )
    check(
        "zero_overhead_ci_brackets_one",
        est.ci_low <= 1.0 <= est.ci_high,
        f"1.0 not in [{est.ci_low:.4f}, {est.ci_high:.4f}]",
    )


def test_monte_carlo_ci_coverage() -> None:
    """The real validation: does the 95% CI actually cover the true
    value ~95% of the time under repeated sampling from the SAME known
    generative model? A single lucky draw (the tests above) cannot
    distinguish a correct procedure from a badly miscalibrated one that
    happens to bracket the true value once. 1000 independent synthetic
    trials give a binomial standard error on the coverage proportion of
    sqrt(0.95*0.05/1000) ~= 0.0069, so accepting [0.90, 0.99] is a wide
    but still meaningful band -- it would catch a doubled or halved
    interval width, a z-vs-t substitution, or an inverted transform,
    while not being flaky from ordinary Monte Carlo noise.
    """
    r_true = 1.2
    n_trials = 1000
    covered = 0
    for trial in range(n_trials):
        records = generate_synthetic(
            r_true=r_true, n_sessions=10, n_blocks=6,
            session_sd=0.04, block_sd=0.06, base_time=1.0, seed=trial,
        )
        est = paired_log_ratio_overhead(records)
        if est.ci_low <= r_true <= est.ci_high:
            covered += 1
    coverage = covered / n_trials
    check(
        "monte_carlo_95pct_ci_coverage_near_nominal",
        0.90 <= coverage <= 0.99,
        f"observed coverage {coverage:.3f} over {n_trials} trials, expected near 0.95",
    )
    print(f"  (Monte Carlo detail: {covered}/{n_trials} = {coverage:.3f} coverage)")


def test_rejects_insufficient_sessions() -> None:
    records = [
        SessionBlockTime(session=0, block=0, time_a=1.0, time_b=1.1),
        SessionBlockTime(session=0, block=1, time_a=1.0, time_b=1.1),
    ]
    raised = False
    try:
        paired_log_ratio_overhead(records)
    except ValueError:
        raised = True
    check("rejects_single_session", raised, "expected ValueError for n_sessions < 2")


def test_rejects_non_positive_time() -> None:
    records = [
        SessionBlockTime(session=0, block=0, time_a=1.0, time_b=1.1),
        SessionBlockTime(session=1, block=0, time_a=0.0, time_b=1.1),
    ]
    raised = False
    try:
        paired_log_ratio_overhead(records)
    except ValueError:
        raised = True
    check("rejects_non_positive_time", raised, "expected ValueError for time_a=0")


def main() -> int:
    test_deterministic_recovery_of_known_overhead()
    test_deterministic_recovery_of_zero_overhead()
    test_monte_carlo_ci_coverage()
    test_rejects_insufficient_sessions()
    test_rejects_non_positive_time()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Analysis pipeline validated against synthetic data with known planted "
        "ratios: point estimates recover the truth, CIs bracket it, and the 95% "
        "CI's Monte Carlo coverage rate is close to nominal -- not just checked "
        "against a single lucky draw."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
