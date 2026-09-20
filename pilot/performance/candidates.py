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
    B0 = gd-tools-coverage addon NOT present at all; `gd-tools test`
    B1 = addon present, autoload registered; `gd-tools test` (no --coverage)
    C  = addon present, autoload registered; `gd-tools test --coverage`

- Nano Coverage has NO B1 (verified 2026-09-20 against
  nano_coverage_godot/integrations/gdunit_hook.gd): the GdUnit4 session
  hook instruments UNCONDITIONALLY in `startup()` the instant it's
  registered in project.godot's `[gdunit4]` hooks/session_hooks --
  there is no flag or env var gating instrumentation once the hook
  exists. So:
    B0 = nano_coverage_godot addon NOT present at all; only gdUnit4
    C  = both addons present, hook registered
    B1 = does not exist for this candidate; never synthesized, per
         the protocol's explicit warning against doing so.

**Corrected 2026-09-20, second Fable review pass (first pilot run was
invalid, see git history and pilot/performance/README.md's postmortem
section):** `addon_sources` was previously keyed per-CANDIDATE, not
per-CONDITION, meaning Nano Coverage's B0 still had the
nano_coverage_godot addon copied in (its .gdextension loaded, its
native classes registered -- confirmed via a leftover scratch
project's extension_list.cfg and a "[NanoCoverage] Editor classes
registered." log line under a B0 run) even though the GdUnit4 hook
itself was correctly left unregistered. That is NOT "collector
absent" per the protocol's own B0 definition (performance-protocol.md
line 11) -- it is closer to the B1 state this module's own docstring
says does not exist for this candidate. Fixed: addon_sources is now
addon_sources_by_condition, so B0 for BOTH candidates only ever copies
the bare test-runner addon (GUT or GdUnit4), never the coverage tool
itself.

**Shader-cache claim corrected 2026-09-20, same review pass:** this
docstring previously claimed the `.godot/shader_cache`/first-run shader
compilation state is cleared before every run, identically across
B0/B1/C. That is FALSE and was never checked against where Godot
actually stores it. `setup_scratch_project()` below only rebuilds the
SCRATCH project directory (fresh `.godot` import cache via `--import`,
rebuilt every run) -- it never touches the OS-level shader cache under
`~/.local/share/godot/app_userdata/<project name>/shader_cache/`, which
is keyed by `project.godot`'s `config/name` and is shared across every
scratch project using that name, i.e. across every candidate and every
condition in this pilot. Confirmed: that directory's mtime predates the
whole 2026-09-20 pilot run, so it was warm (not cleared) for all 200
runs. This does NOT bias the paired B0-vs-C ratios reported here -- the
warm cache is equally warm for every condition of every candidate, so
its cost cancels in the ratio the same way a genuinely-cleared cache
would. But it DOES mean caches are not isolated PER CONDITION as
`docs/benchmarks/performance-protocol.md` (line 48) asks for, and
GdUnit4 also writes logs/objectdb snapshots into that same shared
directory. Before BP10: isolate the OS-level user-data directory per
condition (e.g. override `config/name` or `$HOME`/`$XDG_DATA_HOME` per
scratch project) rather than relying on cancellation-by-symmetry.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
GODOT_BIN = REPO_ROOT / "pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
PERF_ROOT = Path(__file__).parent


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    has_b1: bool
    # Addon dirs to copy, PER CONDITION -- e.g. Nano Coverage's B0 must
    # NOT get the nano_coverage_godot addon at all (true "collector
    # absent"), only gdUnit4; its C condition gets both. Keyed by the
    # name the addon gets copied to under the scratch project's addons/.
    addon_sources_by_condition: dict[str, dict[str, Path]]
    # Where this candidate's test-runner wrapper files live in this
    # repo, and what directory name they must be copied to in the
    # scratch project for that runner to actually find them.
    #
    # **This copy step was MISSING entirely in the first (invalid)
    # version of this module** -- setup_scratch_project() copied
    # workloads/ and drivers/ but never tests_gut/ or tests_gdunit/, so
    # every pilot run found zero tests and exited 0 with nothing
    # measured. Confirmed by an independent Fable review reading the
    # actual .gd-tools/results.xml (tests="0") and Godot logs ("Given
    # directory or file does not exists: tests_gdunit/test_w11.gd") from
    # the first pilot's leftover scratch directories -- exactly BP06's
    # own documented F064 failure mode (GUT exits 0 on zero tests found).
    test_source_dir: Path
    test_dest_name: str
    # project.godot fragments, one per condition that applies to this
    # candidate (never includes "B1" for a candidate where has_b1 is False).
    project_godot_fragments: dict[str, str] = field(default_factory=dict)


GD_TOOLS = CandidateConfig(
    name="gd-tools",
    has_b1=True,
    addon_sources_by_condition={
        "B0": {"gut": REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"},
        "B1": {
            "gut": REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut",
            "gd-tools-coverage": REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage",
        },
        "C": {
            "gut": REPO_ROOT / "pilot/fixtures/cases/f064_zero_requested_tests/addons/gut",
            "gd-tools-coverage": REPO_ROOT / "pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage",
        },
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
    # gd-tools' default test_dirs is ["test", "tests"] (gd_tools/config.py)
    # -- "tests_gut" is NOT scanned by default, so the destination name
    # must be "tests", not a copy of the source directory's own name.
    test_source_dir=PERF_ROOT / "tests_gut",
    test_dest_name="tests",
)

NANO_COVERAGE = CandidateConfig(
    name="nano-coverage",
    has_b1=False,
    addon_sources_by_condition={
        "B0": {"gdUnit4": REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4"},
        "C": {
            "gdUnit4": REPO_ROOT / "pilot/candidates/gdUnit4/addons/gdUnit4",
            "nano_coverage_godot": REPO_ROOT / "pilot/candidates/nano-coverage-godot/demo/addons/nano_coverage_godot",
        },
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
    # run_condition.py invokes "-a tests_gdunit/test_{workload}.gd" --
    # the destination name must match that literally.
    test_source_dir=PERF_ROOT / "tests_gdunit",
    test_dest_name="tests_gdunit",
)


def setup_scratch_project(candidate: CandidateConfig, condition: str, scratch_dir: Path) -> None:
    """Build a fresh scratch project for one candidate/condition,
    clearing any prior .godot import cache -- applied identically
    across every condition. Does NOT clear the OS-level shader cache
    (see module docstring's shader-cache correction)."""
    if condition not in candidate.project_godot_fragments:
        raise ValueError(
            f"{candidate.name} has no {condition} condition "
            f"(has_b1={candidate.has_b1}) -- do not synthesize one"
        )

    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True)

    shutil.copytree(PERF_ROOT / "workloads", scratch_dir / "workloads")
    shutil.copytree(PERF_ROOT / "drivers", scratch_dir / "drivers")
    shutil.copytree(candidate.test_source_dir, scratch_dir / candidate.test_dest_name)

    base_project_godot = (PERF_ROOT / "project.godot").read_text()
    (scratch_dir / "project.godot").write_text(
        base_project_godot + candidate.project_godot_fragments[condition]
    )

    (scratch_dir / "addons").mkdir()
    for addon_name, source in candidate.addon_sources_by_condition[condition].items():
        shutil.copytree(source, scratch_dir / "addons" / addon_name)
