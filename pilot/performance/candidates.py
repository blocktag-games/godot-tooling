"""BP07-09: candidate configurations for the performance study. Two
real, viable coverage-collecting candidates per BP05/BP06 -- gd-tools
(via GUT) and Nano Coverage (via GdUnit4's session hook). Each
candidate gets its own no-coverage baseline under its own test runner
(GUT for gd-tools, GdUnit4 for Nano Coverage) so runner cost is never
mistaken for coverage cost -- GdUnit4 boots a full rendering context
(shader cache generation on first run, confirmed in BP06's F080), gd-
tools' GUT path does not.

Records, per candidate, exactly which of B0/B1/C the protocol's own
rule applies to: "Never synthesize a B1 mode by assuming that
disabling report export disables collection." Verified by reading
source directly, not assumed:

- gd-tools HAS a genuine B1 (verified 2026-09-20 against
  gd_tools/addons/gd-tools-coverage/coverage.gd and gd_tools/
  test_runner.py): the `_GDTCoverage` autoload's own `_ready()` only
  instruments if `GD_TOOLS_COVERAGE_PLAN` is set; the Python CLI only
  sets that env var when `--coverage` is passed, and never touches
  project.godot's `[autoload]` section itself (that's this project's
  own scratch-setup responsibility, same as throughout BP06). So:
    B0 = autoload NOT registered in project.godot; `gd-tools test`
    B1 = autoload registered; `gd-tools test` (no --coverage)
    C  = autoload registered; `gd-tools test --coverage`

- Nano Coverage has NO B1 (verified 2026-09-20 against
  nano_coverage_godot/integrations/gdunit_hook.gd): the GdUnit4 session
  hook instruments UNCONDITIONALLY in `startup()` the instant it's
  registered in project.godot's `[gdunit4]` hooks/session_hooks --
  there is no flag or env var gating instrumentation once the hook
  exists. So:
    B0 = hook NOT registered
    C  = hook registered
    B1 = does not exist for this candidate; never synthesized, per
         the protocol's explicit warning against doing so.

Shader-cache state decision (flagged before any workload was written):
every condition, for every candidate, gets its `.godot` import cache
AND any `.godot/shader_cache`/first-run shader compilation state
cleared before the run, applied IDENTICALLY across B0/B1/C. This is
the same choice already used throughout BP06's corpus-sweep scripts
(clear `.gd-tools`/`.godot` before every invocation) generalized to
Nano Coverage's heavier GdUnit4 boot cost -- a cold-cache cost that is
present in every condition equally cancels in the paired ratio, rather
than risking a "pre-warmed for B0 but not C" asymmetry that would be
invisible in the numbers and unfixable after collection.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    has_b1: bool
    # Paths to vendored addon source directories, keyed by the name
    # they get copied to under the scratch project's addons/.
    addon_sources: dict[str, Path]
    # project.godot fragments, one per condition that applies to this
    # candidate (never includes "B1" for a candidate where has_b1 is False).
    project_godot_fragments: dict[str, str] = field(default_factory=dict)


GD_TOOLS = CandidateConfig(
    name="gd-tools",
    has_b1=True,
    addon_sources={
        "gut": REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut",
        "gd-tools-coverage": REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage",
    },
    project_godot_fragments={
        "B0": """
[editor_plugins]

enabled=PackedStringArray("res://addons/gut/plugin.gd")
""",
        "B1": """
[editor_plugins]

enabled=PackedStringArray("res://addons/gut/plugin.gd")

[autoload]

_GDTCoverage="*res://addons/gd-tools-coverage/coverage.gd"
""",
        "C": """
[editor_plugins]

enabled=PackedStringArray("res://addons/gut/plugin.gd")

[autoload]

_GDTCoverage="*res://addons/gd-tools-coverage/coverage.gd"
""",
    },
)

NANO_COVERAGE = CandidateConfig(
    name="nano-coverage",
    has_b1=False,
    addon_sources={
        "gdUnit4": REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4",
        "nano_coverage_godot": REPO_ROOT / "pilot/candidates/nano-coverage-godot/demo/addons/nano_coverage_godot",
    },
    project_godot_fragments={
        "B0": """
[editor_plugins]

enabled=PackedStringArray("res://addons/gdUnit4/plugin.cfg")
""",
        "C": """
[editor_plugins]

enabled=PackedStringArray("res://addons/nano_coverage_godot/plugin.cfg", "res://addons/gdUnit4/plugin.cfg")

[gdunit4]

hooks/session_hooks=Dictionary[String, bool]({
"res://addons/nano_coverage_godot/integrations/gdunit_hook.gd": true
})

[nano_coverage]

integrations/gdunit4=true
""",
    },
)


def setup_scratch_project(candidate: CandidateConfig, condition: str, scratch_dir: Path) -> None:
    """Build a fresh scratch project for one candidate/condition,
    clearing any prior .godot import cache -- applied identically
    across every condition (see module docstring's shader-cache
    decision)."""
    if condition not in candidate.project_godot_fragments:
        raise ValueError(
            f"{candidate.name} has no {condition} condition "
            f"(has_b1={candidate.has_b1}) -- do not synthesize one"
        )

    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True)

    perf_root = Path(__file__).parent
    shutil.copytree(perf_root / "workloads", scratch_dir / "workloads")
    shutil.copytree(perf_root / "drivers", scratch_dir / "drivers")

    base_project_godot = (perf_root / "project.godot").read_text()
    (scratch_dir / "project.godot").write_text(
        base_project_godot + candidate.project_godot_fragments[condition]
    )

    (scratch_dir / "addons").mkdir()
    for addon_name, source in candidate.addon_sources.items():
        shutil.copytree(source, scratch_dir / "addons" / addon_name)
