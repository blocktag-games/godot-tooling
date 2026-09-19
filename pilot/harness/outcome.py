"""Structured outcome records for harness-driven runs.

BP03 completion evidence requires structured outcome records, not ad
hoc printed text. An Outcome is the one artifact a run produces that
downstream tooling (BP05's parity drivers, BP06's corpus runner) can
consume without re-parsing prose.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Outcome:
    case_id: str
    command: list[str]
    exit_code: int | None
    duration_s: float
    started_at: str
    source_hashes_before: dict[str, str] = field(default_factory=dict)
    source_hashes_after: dict[str, str] = field(default_factory=dict)
    comparator_result: dict[str, Any] | None = None
    status: str = "unknown"  # "pass" | "fail" | "error" | "timeout"
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def write(self, path: Path) -> None:
        path.write_text(self.to_json())

    @classmethod
    def read(cls, path: Path) -> "Outcome":
        return cls(**json.loads(path.read_text()))
