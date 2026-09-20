"""Process execution with enforced timeouts and marker-triggered
termination, for the harness-dependent group-3 fixtures (F065, F067)."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass


@dataclass
class ProcessResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool
    killed: bool


def run(cmd: list[str], cwd: str, timeout_s: float = 30.0) -> ProcessResult:
    """Run `cmd`, enforcing `timeout_s` against the whole process TREE it
    spawns, not just the direct child.

    Launches in its own process group (start_new_session=True) so that on
    timeout, os.killpg() reaches every descendant -- a plain
    `subprocess.run(..., timeout=...)` only ever signals the direct
    child; a grandchild the child spawned (e.g. gd-tools test spawning a
    Godot subprocess) is left running, orphaned, with no owner left to
    reap it. Confirmed as a real defect (F067): running gd-tools test
    against an artificially slow test with a short timeout_s left the
    Godot process alive and running well after this function returned,
    under the version of run() that used plain subprocess.run().
    """
    start = time.monotonic()
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        return ProcessResult(
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_s=time.monotonic() - start,
            timed_out=False,
            killed=False,
        )
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass  # already exited between the timeout firing and here
        stdout, stderr = proc.communicate()
        return ProcessResult(
            exit_code=None,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_s=time.monotonic() - start,
            timed_out=True,
            killed=False,
        )


def run_and_terminate_on_marker(
    cmd: list[str], cwd: str, marker: str, timeout_s: float = 30.0
) -> ProcessResult:
    """Launch a process and send SIGTERM as soon as `marker` appears on its
    stdout, to test graceful-interruption behavior at a known point (F065).
    Falls back to SIGKILL if the process doesn't exit within 5s of the
    terminate signal, or if the overall timeout is exceeded first.
    """
    start = time.monotonic()
    deadline = start + timeout_s
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )
    killed = False
    stdout_lines: list[str] = []
    assert proc.stdout is not None

    for line in proc.stdout:
        stdout_lines.append(line)
        if marker in line:
            proc.terminate()
            killed = True
            break
        if time.monotonic() > deadline:
            proc.kill()
            break

    try:
        remaining_stdout, stderr = proc.communicate(timeout=max(0.1, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        proc.kill()
        remaining_stdout, stderr = proc.communicate()

    stdout_lines.append(remaining_stdout or "")
    return ProcessResult(
        exit_code=proc.returncode,
        stdout="".join(stdout_lines),
        stderr=stderr or "",
        duration_s=time.monotonic() - start,
        timed_out=False,
        killed=killed,
    )
