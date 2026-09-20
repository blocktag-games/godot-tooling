#!/usr/bin/env python3
"""BP08: the H=0 "minimal documented launcher" of profiling-protocol.md's
factorial observer experiment ("Minimal documented launcher with the
same child command and required result capture"). Deliberately as thin
as possible: no CandidateConfig, no ConditionResult dataclass, no
behavior_ok/coverage_artifact_ok checks, no print-formatted reporting --
just the same runner.run() call against the identical command, printing
one number.

Contrast with run_condition.py (the H=1 "full benchmark orchestration"
launcher for the same command). Used by harness_overhead_check.py to
measure the H (harness) main effect for BP08's pilot observer matrix.

Usage: minimal_launcher.py <scratch_dir> <cmd...>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "harness"))
from runner import run  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: minimal_launcher.py <scratch_dir> <cmd...>", file=sys.stderr)
        return 2
    scratch_dir = sys.argv[1]
    cmd = sys.argv[2:]
    result = run(cmd, cwd=scratch_dir, timeout_s=120)
    print(f"{result.duration_s:.4f}")
    return 0 if result.exit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
