#!/usr/bin/env python3
"""BP02 ground-truth check for F062 (injected instrumentation failure),
generic fault-injection half. Committed so this is a real, reproducible
check rather than the ad hoc inline test it used to be.

The primary, real-tool realization of this requirement is F008 (see
oracles/F062.json and oracles/F008.json) -- gd-tools' own gdtoolkit
parser rejects a legitimate file and silently drops it with no durable
record. This script covers the second, tool-independent half: proving
pilot/harness/faults.py's make_unwritable() actually produces a
detectable write failure that a future adapter wrapper (for a tool that
instruments by rewriting files in place, unlike gd-tools' in-memory
reload(true) approach) would need to catch and report explicitly.

Run: python3 check.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "harness"))
from faults import make_unwritable, restore_writable  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "subject.gd"
        original = "extends RefCounted\n\nstatic func run() -> int:\n\treturn 1\n"
        target.write_text(original)

        make_unwritable(target)
        write_failed = False
        try:
            target.write_text("extends RefCounted\n\nstatic func run() -> int:\n\treturn 2\n")
        except PermissionError:
            write_failed = True
        finally:
            restore_writable(target)

        check("instrumentation_write_raises_permission_error", write_failed, "expected PermissionError")
        check(
            "source_left_unchanged_after_failed_write",
            target.read_text() == original,
            target.read_text(),
        )

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "F062 fault-injection primitive confirmed: an unwritable source file "
        "produces a real, catchable write failure with no partial corruption. "
        "See oracles/F008.json for the primary real-tool realization of this "
        "requirement against gd-tools 0.4.0 itself."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
