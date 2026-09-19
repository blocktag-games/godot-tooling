"""Isolated workspace creation for harness-driven runs.

BP03 completion evidence requires isolated workspaces: a run must
operate on its own copy of a fixture case, not on the committed source
tree in place, so a run's side effects (instrumentation, mutated
files, crashes) can never contaminate the fixture itself or a
different run's workspace.
"""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Workspace:
    root: Path
    source_hashes: dict[str, str] = field(default_factory=dict)


def _hash_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for p in root.rglob("*"):
        if p.is_file():
            hashes[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def create(case_dir: Path, workspace_root: Path | None = None) -> Workspace:
    """Copy a fixture case directory into a fresh isolated temp
    directory and record every file's hash before any run touches it.
    """
    dest = Path(tempfile.mkdtemp(dir=workspace_root, prefix="ws-"))
    shutil.copytree(case_dir, dest, dirs_exist_ok=True)
    return Workspace(root=dest, source_hashes=_hash_tree(dest))


def verify_unchanged(ws: Workspace, paths: list[str] | None = None) -> dict[str, bool]:
    """Check whether files still match their hash recorded at creation
    time. Used for the source-restoration check (correctness-protocol.md
    step 6): did a run leave the workspace's source files unmodified?

    A missing file is reported as unchanged=False, not silently skipped.
    """
    check_paths = paths if paths is not None else list(ws.source_hashes.keys())
    result: dict[str, bool] = {}
    for rel in check_paths:
        p = ws.root / rel
        if not p.exists():
            result[rel] = False
            continue
        current = hashlib.sha256(p.read_bytes()).hexdigest()
        result[rel] = current == ws.source_hashes.get(rel)
    return result


def cleanup(ws: Workspace) -> None:
    shutil.rmtree(ws.root, ignore_errors=True)
