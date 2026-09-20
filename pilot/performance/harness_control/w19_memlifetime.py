#!/usr/bin/env python3
"""W19: Memory-lifetime child. Allocates a known amount of memory,
ACTUALLY COMMITS it (touches every page -- a bare bytearray(n) allocation
can be satisfied by the allocator's zero-page/COW tricks on Linux
without committing real RSS, which would make this workload measure
virtual reservation instead of the resident-memory lifecycle it's
meant to expose), holds it for a known retention window so an external
sampler can observe the peak during that window, then releases it and
exits.

Per docs/benchmarks/performance-protocol.md's Resources section: this
workload's own behavior check only confirms the ALLOCATION LIFECYCLE
(did it allocate, hold, and release on schedule) -- it does NOT itself
measure or claim a specific RSS/PSS/cgroup-memory.peak value, since
which of those metrics is even available has to be established
per-machine (see the protocol's explicit distinction between per-
process peak RSS, sampled simultaneous RSS/PSS, and cgroup peak charged
memory -- these measure different quantities and none is assumed here).

Usage: w19_memlifetime.py <alloc_mb> <retain_seconds>
"""
import sys
import time

PAGE_SIZE = 4096


def touch_all_pages(buf: bytearray) -> None:
    for offset in range(0, len(buf), PAGE_SIZE):
        buf[offset] = 1  # force a real write to this page, not just a reservation


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: w19_memlifetime.py <alloc_mb> <retain_seconds>", file=sys.stderr)
        return 2
    alloc_mb = int(sys.argv[1])
    retain_seconds = float(sys.argv[2])

    alloc_bytes = alloc_mb * 1024 * 1024
    buf = bytearray(alloc_bytes)
    touch_all_pages(buf)
    print(f"allocated_mb={alloc_mb}", flush=True)

    time.sleep(retain_seconds)
    print(f"retained_seconds={retain_seconds}", flush=True)

    del buf
    print("released=true", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
