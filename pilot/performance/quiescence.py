#!/usr/bin/env python3
"""BP10: the machine-quiescence check docs/benchmarks/performance-
protocol.md's amended item 3 requires immediately before each session
starts: "a concrete, actually-measurable quiescence check... idle CPU
utilization below a stated threshold... sustained for a stated
duration... measured directly (/proc/stat or equivalent), not merely a
rest interval assumed sufficient."

Read literally, "idle CPU utilization below a threshold" is backwards
(a QUIET machine has HIGH idle%, not low) -- the frozen protocol text's
clear intent, and what this module implements, is: BUSY (non-idle) CPU
utilization must stay BELOW a stated threshold (e.g. 5%) for a stated
duration (e.g. 60s) before a session is allowed to start. This module
does not silently reinterpret the frozen document; it implements the
sensible reading and states the resolved ambiguity here rather than
leaving it to whoever runs this next to guess.

No thermal telemetry exists on this machine (confirmed: `upower`
exposes battery state only) -- thermal quiescence is NOT claimed or
checked, exactly as the protocol's own text already acknowledges.

Run standalone to sanity-check current machine state:
    python3 quiescence.py
"""
from __future__ import annotations

import sys
import time


def _read_cpu_times() -> tuple[int, int]:
    """(idle+iowait, total) jiffies since boot, from /proc/stat's
    aggregate 'cpu' line (all cores combined)."""
    with open("/proc/stat") as f:
        line = f.readline()
    parts = [int(x) for x in line.split()[1:]]
    # user nice system idle iowait irq softirq steal guest guest_nice
    idle = parts[3] + parts[4]
    total = sum(parts)
    return idle, total


def measure_busy_percent(window_s: float = 60.0, sample_interval_s: float = 5.0) -> tuple[float, float]:
    """Samples /proc/stat repeatedly over `window_s`, returning
    (mean_busy_pct, max_busy_pct) across the sampling intervals within
    that window. A single before/after snapshot over the whole window
    would average away a brief spike; per-interval sampling catches it
    (reported as max_busy_pct)."""
    n_samples = max(2, round(window_s / sample_interval_s))
    busy_pcts = []
    prev_idle, prev_total = _read_cpu_times()
    for _ in range(n_samples):
        time.sleep(sample_interval_s)
        idle, total = _read_cpu_times()
        d_idle, d_total = idle - prev_idle, total - prev_total
        busy_pcts.append(100.0 * (1.0 - d_idle / d_total) if d_total > 0 else 0.0)
        prev_idle, prev_total = idle, total
    return sum(busy_pcts) / len(busy_pcts), max(busy_pcts)


def wait_for_quiescence(
    busy_threshold_pct: float = 5.0,
    window_s: float = 60.0,
    sample_interval_s: float = 5.0,
    max_wait_s: float = 600.0,
) -> dict:
    """Blocks until a `window_s`-long sampling window shows max busy%
    at or below `busy_threshold_pct`, or raises RuntimeError once
    `max_wait_s` total has elapsed without achieving that -- this is a
    GATE, not a best-effort check: per the protocol, a session must not
    start on an unverified assumption of quiet, and an unattended
    10-session study should stop and surface the problem rather than
    silently collect data on a noisy machine.

    Returns a dict recording what was actually measured, for the
    session's own record (not just pass/fail).
    """
    deadline = time.monotonic() + max_wait_s
    attempts = []
    while True:
        mean_busy, max_busy = measure_busy_percent(window_s, sample_interval_s)
        attempts.append({"mean_busy_pct": mean_busy, "max_busy_pct": max_busy})
        if max_busy <= busy_threshold_pct:
            return {
                "quiescent": True,
                "busy_threshold_pct": busy_threshold_pct,
                "window_s": window_s,
                "attempts": attempts,
            }
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"Machine did not reach quiescence (busy% <= {busy_threshold_pct}% for "
                f"{window_s}s) within {max_wait_s}s -- {len(attempts)} attempt(s) tried, "
                f"last max_busy_pct={max_busy:.1f}%. Aborting rather than proceeding on an "
                f"unverified assumption of quiet, per performance-protocol.md's amended item 3. "
                f"Check for competing processes (ps aux --sort=-pcpu) before retrying."
            )
        print(
            f"  not yet quiescent (mean={mean_busy:.1f}%, max={max_busy:.1f}%, "
            f"threshold={busy_threshold_pct}%) -- retrying...",
            file=sys.stderr,
        )


def main() -> int:
    print(f"Sampling current machine busy% over a 15s window (quick check, not the full {60}s gate)...")
    mean_busy, max_busy = measure_busy_percent(window_s=15.0, sample_interval_s=3.0)
    print(f"mean_busy_pct={mean_busy:.2f}% max_busy_pct={max_busy:.2f}%")
    print("(This is a diagnostic snapshot only -- the real gate uses window_s=60.0 by default.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
