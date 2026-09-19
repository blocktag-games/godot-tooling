#!/usr/bin/env python3
"""Synthetic report-writer subject for F065.

Models the correct pattern for a process that produces a report file:
write to a temp path first, only rename it to the final path once the
data is complete. Sleeps between the two phases so a harness can
interrupt it at a known, marked point and verify that no
finished-looking final artifact can appear as a result -- regardless of
where in its work the process was killed.
"""
import json
import sys
import time
from pathlib import Path

out_dir = Path(sys.argv[1])
tmp_path = out_dir / "report.json.tmp"
final_path = out_dir / "report.json"

tmp_path.write_text(json.dumps({"status": "partial", "files": []}))
print("MARKER_PARTIAL_WRITTEN", flush=True)

time.sleep(5)  # window for the harness to terminate here

tmp_path.write_text(json.dumps({"status": "complete", "files": ["a.gd", "b.gd"]}))
tmp_path.rename(final_path)  # atomic on POSIX: no window where a partial rename is observable
print("MARKER_DONE", flush=True)
