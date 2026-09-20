#!/usr/bin/env python3
"""W17: Log-volume child. Fixed stdout/stderr byte counts, in either a
single burst or many small chunks (the two "production patterns" this
workload exists to distinguish, per docs/benchmarks/workload-catalog.tsv)
-- exercises whether the harness's own capture path (large pipe reads
vs. many small ones) drops or truncates bytes under backpressure. This
is the performance-measurement cousin of BP06's F078 (large stdout/
stderr volume, tier-2, deferred): F078 asks whether backpressure causes
a deadlock or silent evidence loss at all; this workload asks what it
costs when it doesn't.

Emits a deterministic repeating byte pattern (not random and not all
zeros) so the exact CONTENT, not just the count, can be verified
byte-for-byte by the behavior check -- catches a truncation that
happens to preserve the total byte count (e.g. a dropped-then-padded
chunk) that a length-only check would miss.

Usage: w17_logvolume.py <stdout_bytes> <stderr_bytes> <burst|chunked> [chunk_size]
"""
import sys

PATTERN = b"0123456789ABCDEF"  # 16 bytes, repeats cleanly, easy to verify by offset % 16


def make_bytes(n: int) -> bytes:
    full, remainder = divmod(n, len(PATTERN))
    return PATTERN * full + PATTERN[:remainder]


def emit(stream, data: bytes, mode: str, chunk_size: int) -> None:
    if mode == "burst":
        stream.buffer.write(data)
    elif mode == "chunked":
        for i in range(0, len(data), chunk_size):
            stream.buffer.write(data[i : i + chunk_size])
            stream.buffer.flush()
    else:
        raise ValueError(f"unknown mode: {mode!r}")
    stream.buffer.flush()


def main() -> int:
    if len(sys.argv) not in (4, 5):
        print("usage: w17_logvolume.py <stdout_bytes> <stderr_bytes> <burst|chunked> [chunk_size]", file=sys.stderr)
        return 2
    stdout_bytes = int(sys.argv[1])
    stderr_bytes = int(sys.argv[2])
    mode = sys.argv[3]
    chunk_size = int(sys.argv[4]) if len(sys.argv) == 5 else 256

    emit(sys.stdout, make_bytes(stdout_bytes), mode, chunk_size)
    emit(sys.stderr, make_bytes(stderr_bytes), mode, chunk_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
