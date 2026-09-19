"""Report comparison logic for the coverage benchmark harness.

Compares a normalized "actual" coverage report against a hand-reviewed
oracle's obligations, per correctness-protocol.md's coverage accounting
section. Never infers success from absence: a missing file or a stale
source hash is reported explicitly, never silently folded into a hit
or miss count.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


class MalformedReportError(Exception):
    """Raised when an actual report cannot be understood at all."""


def load_actual_report(path: Path) -> dict:
    """Read and parse an actual report JSON file.

    Raises MalformedReportError on a missing file or invalid JSON --
    this must never be interpreted as zero coverage or as success by a
    caller further up the pipeline.
    """
    try:
        text = path.read_text()
    except OSError as e:
        raise MalformedReportError(f"cannot read report file {path}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise MalformedReportError(f"report {path} is not valid JSON: {e}") from e


@dataclass
class Obligation:
    file: str
    sha256: str
    line: int
    expected_hit: bool


@dataclass
class ComparisonResult:
    status: str  # "match" | "mismatch"
    matched: list = field(default_factory=list)
    false_hits: list = field(default_factory=list)         # hit reported, expected not-hit
    missing_hits: list = field(default_factory=list)       # expected hit, never reported
    missing_files: list = field(default_factory=list)
    stale_files: list = field(default_factory=list)        # report's file hash != current source
    oracle_stale_files: list = field(default_factory=list) # oracle's own expected hash != current source

    @property
    def is_clean(self) -> bool:
        return not (
            self.false_hits
            or self.missing_hits
            or self.missing_files
            or self.stale_files
            or self.oracle_stale_files
        )


def compare(obligations: list[Obligation], actual: dict, source_root: Path) -> ComparisonResult:
    """Compare obligations against an actual report of the form
    {"files": [{"path": str, "sha256": str, "hits": {"<line>": count}}]}.

    Raises MalformedReportError if `actual` doesn't even have the
    minimum required shape -- this must never be interpreted as zero
    coverage or as success. Raises MalformedReportError if a single
    file's obligations declare inconsistent sha256 values -- that is a
    broken oracle, not a comparable case.
    """
    result = ComparisonResult(status="match")
    if not isinstance(actual, dict) or "files" not in actual:
        raise MalformedReportError("actual report missing required 'files' key")

    actual_by_path = {}
    for f in actual["files"]:
        if "path" not in f or "sha256" not in f or "hits" not in f:
            raise MalformedReportError(f"actual file entry missing required keys: {f}")
        actual_by_path[f["path"]] = f

    obligations_by_file: dict[str, list[Obligation]] = {}
    for o in obligations:
        obligations_by_file.setdefault(o.file, []).append(o)

    for file_path, obls in obligations_by_file.items():
        full_path = source_root / file_path
        current_hash = hashlib.sha256(full_path.read_bytes()).hexdigest() if full_path.exists() else None

        oracle_hashes = {o.sha256 for o in obls}
        if len(oracle_hashes) > 1:
            raise MalformedReportError(
                f"obligations for {file_path} declare inconsistent sha256 values: {oracle_hashes}"
            )
        oracle_sha = next(iter(oracle_hashes))

        if current_hash is not None and oracle_sha != current_hash:
            # The oracle itself is bound to a different version of this
            # file than what's actually on disk right now -- distinct
            # from the report being stale, and checked first, since
            # nothing else about this file is trustworthy if the oracle
            # doesn't even match current source.
            result.oracle_stale_files.append(file_path)
            continue

        if file_path not in actual_by_path:
            result.missing_files.append(file_path)
            continue

        entry = actual_by_path[file_path]
        if current_hash is not None and entry["sha256"] != current_hash:
            result.stale_files.append(file_path)
            continue

        hits = entry["hits"]
        for o in obls:
            line_key = str(o.line)
            was_hit = line_key in hits and hits[line_key] > 0
            if o.expected_hit and was_hit:
                result.matched.append((file_path, o.line))
            elif o.expected_hit and not was_hit:
                result.missing_hits.append((file_path, o.line))
            elif not o.expected_hit and was_hit:
                result.false_hits.append((file_path, o.line))
            else:
                result.matched.append((file_path, o.line))  # correctly not hit

    if not result.is_clean:
        result.status = "mismatch"
    return result
