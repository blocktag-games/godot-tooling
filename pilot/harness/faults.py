"""Fault-injection helpers for harness-dependent group-3 fixtures."""
from __future__ import annotations

import stat
from pathlib import Path


def make_unwritable(path: Path) -> None:
    """Remove write permission, simulating an instrumentation step that
    cannot rewrite the file in place (F062)."""
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def restore_writable(path: Path) -> None:
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def make_dir_unwritable(path: Path) -> None:
    path.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def restore_dir_writable(path: Path) -> None:
    path.chmod(
        stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        | stat.S_IRGRP | stat.S_IXGRP
        | stat.S_IROTH | stat.S_IXOTH
    )


def truncate(path: Path, keep_bytes: int) -> None:
    data = path.read_bytes()
    path.write_bytes(data[:keep_bytes])
