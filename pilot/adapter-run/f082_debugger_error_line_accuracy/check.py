#!/usr/bin/env python3
"""BP11: F082, debugger-protocol error-line accuracy under
instrumentation, against real gd-tools-cli 0.4.0 AND real Nano
Coverage -- extending F057 (which only checked gd-tools, and only
checked raw stderr text, not the debugger-observable protocol) in two
directions at once.

F057's own notes explicitly separated two questions: "the engine-only
half" (does the raw runtime diagnostic shift under gd-tools -- F057,
already answered: yes) from a harder, BP11-scoped question, quoted
here in full: "whether a debugger's own breakpoint-binding logic,
likely keyed by its own source-position bookkeeping rather than
blindly trusting the running script's live line numbers, is similarly
confused by the shift, or already immune to it via some other
mechanism."

**This fixture answers a closely related but NARROWER question than
that one, and says so plainly rather than overclaiming F082 closed.**
It confirms that the STRUCTURED "error" message on Godot's own remote
debug wire protocol -- the exact data source the Godot Editor's
Debugger panel and VS Code's `godot-tools` extension both render --
reports the same shifted line the raw stderr text already showed, for
BOTH candidates. It does NOT test explicit breakpoint BINDING (setting
a breakpoint via `-b file::line` or the Editor's own gutter click and
confirming execution actually pauses at the intended statement): a
real `-b` breakpoint did not activate against a minimal, receive-only
socket client built for this project (confirmed directly, several
variants tried -- see this directory's README) -- Godot's real
debugger clients evidently perform additional protocol-level
configuration this project did not reverse-engineer. Testing genuine
breakpoint binding would need either a real Godot Editor GUI session
(infeasible in this environment: no `xdotool`/`scrot`/`import`
installed, installing them needs sudo not cached this session, and the
only available X display is the user's own live interactive desktop,
not appropriate to launch automated GUI tests on) or a fuller two-way
debugger-protocol implementation, which was judged disproportionate
scope for this verification. That remains open.

What IS answered, for the first time for either candidate: the
"pause on unhandled error" debugger behavior -- which requires NO
debugger-side configuration, fires automatically the instant
`--remote-debug` is attached, and is exactly what a developer watching
the Debugger panel while their covered tests run would see -- reports
the WRONG line under both gd-tools and Nano Coverage. Nano Coverage's
own shift was not previously known or checked anywhere in this
project; F057's own fixture only ever exercised gd-tools.

Mechanism as reproduced here:
- gd-tools: confirmed already by F057 -- coverage.gd's
  `_inject_trackers()` inserts tracker-call lines directly into the
  script's in-memory `source_code` string before `Script.reload(true)`.
- Nano Coverage: mechanism not directly inspected here (it is a native
  GDExtension; its source is not GDScript this project can read the
  same way), but the observed symptom is IDENTICAL in shape: the true
  line-4 division-by-zero reports at line 5 once Nano Coverage's
  session hook has run `instrument_all_scripts()` -- a shift of
  exactly +1, matching gd-tools' own shift magnitude for this same
  single-tracker fixture. Two separate `GDScript::reload` parse-time
  warnings are observed for the same file (at line 4 and line 5),
  consistent with the file being reloaded once before and once after
  in-memory instrumentation, the same two-pass pattern F057 already
  established for gd-tools.

Run: python3 check.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "pilot/performance"))
from godot_debug_protocol import parse_packets, capture_session  # noqa: E402
from candidates import NANO_COVERAGE, setup_scratch_project, GODOT_BIN  # noqa: E402

GD_TOOLS_BIN = REPO_ROOT / "pilot/gd-tools/.venv/bin/gd-tools"
GUT_SOURCE = REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"
GD_TOOLS_COVERAGE_SOURCE = REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage"

TRUE_ERROR_LINE = 4  # subject.gd's "return 100 / divisor" line

SUBJECT_GD = "extends RefCounted\n\nstatic func run(divisor: int) -> int:\n\treturn 100 / divisor\n"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"PASS {name}")
    else:
        msg = f"FAIL {name}: {detail}"
        print(msg)
        FAILURES.append(msg)


def find_reported_line(packets: list) -> int | None:
    """The final real runtime-error packet: ["error", 1, [..., source_file,
    source_function, source_line, "Division by zero...", ...]]. Reload-time
    parser warnings (INTEGER_DIVISION) are skipped -- they're a distinct,
    earlier event, not the runtime error itself."""
    for p in packets:
        if isinstance(p, list) and len(p) >= 3 and p[0] == "error":
            args = p[2]
            if len(args) >= 8 and isinstance(args[7], str) and "Division by zero" in args[7]:
                return args[6]  # source_line field
    return None


def run_with_debug_capture(cmd: list[str], cwd: str, env: dict, port: int, listen_seconds: float = 10.0) -> list:
    result_holder: dict = {}

    def listener() -> None:
        result_holder["data"] = capture_session(port, listen_seconds)

    t = threading.Thread(target=listener)
    t.start()
    import time
    time.sleep(0.5)  # let the listener bind before Godot tries to connect
    subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, timeout=30)
    t.join(timeout=listen_seconds + 5)
    return parse_packets(result_holder.get("data", b""))


def check_uninstrumented() -> int | None:
    scratch = Path("/tmp/f082-raw")
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    (scratch / "project.godot").write_text('config_version=5\n\n[application]\n\nconfig/name="f082-raw"\n')
    (scratch / "subject.gd").write_text(SUBJECT_GD)
    (scratch / "probe.gd").write_text(
        "extends SceneTree\n"
        "func _initialize() -> void:\n"
        "\tcall_deferred(\"_after\")\n"
        "func _after() -> void:\n"
        "\tvar subject = load(\"res://subject.gd\")\n"
        "\tsubject.run(0)\n"
        "\tquit(0)\n"
    )
    subprocess.run([str(GODOT_BIN), "--headless", "--path", str(scratch), "--import"], capture_output=True, timeout=30)
    env = dict(os.environ)
    packets = run_with_debug_capture(
        [str(GODOT_BIN), "--headless", "--path", str(scratch), "--script", "probe.gd", "--remote-debug", "tcp://127.0.0.1:6301"],
        cwd=str(scratch), env=env, port=6301,
    )
    return find_reported_line(packets)


def check_gd_tools() -> int | None:
    scratch = Path("/tmp/f082-gdtools")
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    (scratch / "subject").mkdir()
    (scratch / "subject" / "subject.gd").write_text(SUBJECT_GD)
    (scratch / "tests").mkdir()
    (scratch / "tests" / "test_subject.gd").write_text(
        "extends GutTest\nfunc test_passes() -> void:\n\tvar subject = load(\"res://subject/subject.gd\")\n\tassert_eq(subject.run(4), 25)\n"
    )
    (scratch / "probe.gd").write_text(
        "extends SceneTree\n"
        "func _initialize() -> void:\n"
        "\tcall_deferred(\"_after\")\n"
        "func _after() -> void:\n"
        "\tvar subject = load(\"res://subject/subject.gd\")\n"
        "\tsubject.run(0)\n"
        "\tquit(0)\n"
    )
    (scratch / "addons").mkdir()
    shutil.copytree(GUT_SOURCE, scratch / "addons" / "gut")
    shutil.copytree(GD_TOOLS_COVERAGE_SOURCE, scratch / "addons" / "gd-tools-coverage")
    (scratch / "project.godot").write_text(
        'config_version=5\n\n[application]\n\nconfig/name="f082-gdtools"\n\n'
        '[editor_plugins]\n\nenabled=PackedStringArray("res://addons/gut/plugin.gd")\n\n'
        '[autoload]\n\n_GDTCoverage="*res://addons/gd-tools-coverage/coverage.gd"\n'
    )
    subprocess.run([str(GODOT_BIN), "--headless", "--path", str(scratch), "--import"], capture_output=True, timeout=30)

    env = dict(os.environ)
    env["GODOT_BIN"] = str(GODOT_BIN)
    result = subprocess.run([str(GD_TOOLS_BIN), "test", "--coverage"], cwd=str(scratch), env=env, capture_output=True, text=True, timeout=60)
    check("gd_tools_real_run_passed", "All 1 test(s) passed" in result.stdout, result.stdout)
    plan_path = scratch / ".gd-tools/coverage/plan.json"
    check("gd_tools_real_plan_json_produced", plan_path.exists(), "plan.json missing")

    env2 = dict(os.environ)
    env2["GD_TOOLS_COVERAGE_PLAN"] = str(plan_path)
    packets = run_with_debug_capture(
        [str(GODOT_BIN), "--headless", "--path", str(scratch), "--script", "probe.gd", "--remote-debug", "tcp://127.0.0.1:6302"],
        cwd=str(scratch), env=env2, port=6302,
    )
    return find_reported_line(packets)


def check_nano_coverage() -> int | None:
    scratch = Path("/tmp/f082-nano")
    setup_scratch_project(NANO_COVERAGE, "C", scratch)
    (scratch / "subject").mkdir(exist_ok=True)
    (scratch / "subject" / "subject.gd").write_text(SUBJECT_GD)
    (scratch / "tests_gdunit" / "test_f082.gd").write_text(
        "extends GdUnitTestSuite\nfunc test_f082_trigger_error() -> void:\n\tvar subject = load(\"res://subject/subject.gd\")\n\tsubject.run(0)\n"
    )
    subprocess.run([str(GODOT_BIN), "--headless", "--path", str(scratch), "--import"], capture_output=True, timeout=30)

    env = dict(os.environ)
    packets = run_with_debug_capture(
        [str(GODOT_BIN), "--path", str(scratch), "-s", "-d", "--remote-debug", "tcp://127.0.0.1:6303",
         "res://addons/gdUnit4/bin/GdUnitCmdTool.gd", "-a", "tests_gdunit/test_f082.gd"],
        cwd=str(scratch), env=env, port=6303, listen_seconds=20.0,
    )
    return find_reported_line(packets)


def main() -> int:
    uninstrumented = check_uninstrumented()
    check("uninstrumented_reports_true_line", uninstrumented == TRUE_ERROR_LINE, f"got {uninstrumented}")

    gd_tools_line = check_gd_tools()
    check("gd_tools_debugger_protocol_reports_a_line", gd_tools_line is not None, "no error packet captured")
    if gd_tools_line is not None and uninstrumented is not None:
        check("gd_tools_debugger_protocol_line_is_shifted", gd_tools_line != uninstrumented,
              f"expected shift from {uninstrumented}, both were {gd_tools_line}")

    nano_line = check_nano_coverage()
    check("nano_coverage_debugger_protocol_reports_a_line", nano_line is not None, "no error packet captured")
    if nano_line is not None and uninstrumented is not None:
        check("nano_coverage_debugger_protocol_line_is_shifted", nano_line != uninstrumented,
              f"expected shift from {uninstrumented}, both were {nano_line}")

    print()
    print(f"true source line: {TRUE_ERROR_LINE}")
    print(f"uninstrumented debugger-protocol report: {uninstrumented}")
    print(f"gd-tools debugger-protocol report: {gd_tools_line}")
    print(f"nano-coverage debugger-protocol report: {nano_line}")
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  {f}")
        return 1
    print(
        "Confirmed against real gd-tools-cli 0.4.0 AND real Nano Coverage: Godot's own "
        "remote debug protocol -- the exact data source the Editor's Debugger panel and "
        "VS Code's godot-tools extension both render -- reports a SHIFTED line for an "
        "unhandled runtime error under coverage instrumentation from EITHER candidate, "
        "not just the raw stderr text F057 already established for gd-tools alone. "
        "Explicit breakpoint BINDING (a developer's own -b/gutter-set breakpoint) remains "
        "untested -- see this file's module docstring for why and what would be needed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
