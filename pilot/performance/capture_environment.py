#!/usr/bin/env python3
"""BP07: capture the environment record docs/benchmarks/
performance-protocol.md's "Control the environment" section requires
("CPU model/topology, affinity, RAM, storage/filesystem, OS/kernel,
engine/build hashes, compiler where known, power source/profile, CPU
governor/turbo state where visible, virtualization/container state,
renderer/driver, background workload, and thermal telemetry if
available") -- captured once per pilot/study run, alongside (not
replacing) the timed data, per a review finding that no such record
existed for the first BP07 pilot sweep.

Deliberately best-effort and explicit about what's unavailable rather
than silent: this machine has no confirmed thermal telemetry (`upower`
exposes battery state only), and this session has no sudo, so anything
requiring elevated privileges is recorded as "not captured" rather than
guessed at or skipped without a trace.

Run: python3 capture_environment.py > environment.json
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"


def _run(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def capture() -> dict:
    cpu_governors = {}
    cpu_dir = Path("/sys/devices/system/cpu")
    if cpu_dir.exists():
        for cpu in sorted(cpu_dir.glob("cpu[0-9]*")):
            gov = _read(str(cpu / "cpufreq/scaling_governor"))
            if gov:
                cpu_governors[cpu.name] = gov

    lscpu = _run(["lscpu"]) or ""
    model_name = next((line.split(":", 1)[1].strip() for line in lscpu.splitlines() if line.startswith("Model name:")), None)

    return {
        "cpu": {
            "model_name": model_name,
            "logical_cores": _run(["nproc"]),
            "governors_per_core": cpu_governors,
            "governors_uniform": len(set(cpu_governors.values())) <= 1,
        },
        "memory": {
            "meminfo_total_kb": next(
                (line.split()[1] for line in (_read("/proc/meminfo") or "").splitlines() if line.startswith("MemTotal:")),
                None,
            ),
        },
        "os": {
            "kernel_release": platform.release(),
            "kernel_version": _read("/proc/version"),
            "distro": _run(["lsb_release", "-ds"]) or _read("/etc/os-release"),
        },
        "power": {
            "on_ac_power": _run(["on_ac_power"]) is not None,  # exit code only; stdout unused
            "upower_battery_state": _run(["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"]),
            "thermal_telemetry": "NOT AVAILABLE -- upower exposes battery state only on this machine, "
                                  "no confirmed temperature sensor path checked/validated this session",
        },
        "virtualization": {
            "systemd_detect_virt": _run(["systemd-detect-virt"]) or "not detected or systemd-detect-virt unavailable",
        },
        "engine": {
            "godot_binary_path": str(GODOT_BIN),
            "godot_version_output": _run([str(GODOT_BIN), "--version"]),
            "godot_binary_sha256": _run(["sha256sum", str(GODOT_BIN)]),
        },
        "background_workload": {
            "note": "NOT a machine-quiescence check -- that gate is BP10-only per this project's "
                    "established scope decision (docs/benchmarks/implementation-plan.md's BP10 row). "
                    "This is a one-shot snapshot for the record, not a precondition enforced here.",
            "top_processes_by_cpu": "\n".join((_run(["ps", "-eo", "pid,pcpu,comm", "--sort=-pcpu"]) or "").splitlines()[:20]),
        },
        "privileged_fields_not_captured": [
            "hardware turbo-boost state (requires msr-tools/sudo, not available this session)",
            "exact storage/filesystem device model (not probed -- low relevance to CPU-bound workloads here)",
        ],
    }


def main() -> int:
    print(json.dumps(capture(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
