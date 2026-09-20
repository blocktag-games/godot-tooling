# BP02 tier-0 fixtures

Part of [BP02](../../docs/benchmarks/implementation-plan.md): implement the first
independent fixtures and oracles, built in the three groups from the
implementation plan's tier-0 build order.

No coverage tool touches anything here. This only establishes and verifies the
uninstrumented ground truth per [correctness-protocol.md](../../docs/benchmarks/correctness-protocol.md):
each fixture is a small GDScript program, each oracle in `oracles/` is a
hand-traced statement of exactly which lines/branches/functions execute for
which named inputs, bound to the fixture file's exact SHA-256 hash.

## Group 1 — pure GDScript (no live process lifecycle, no harness)

| ID | Case | Files |
| --- | --- | --- |
| F001 | Never-loaded selected file | `cases/f001_never_loaded/{loaded,unloaded}.gd` |
| F002 | Never-called function | `cases/f002_never_called/subject.gd` |
| F010 | Straight-line body | `cases/f010_straight_line/subject.gd` |
| F012 | Multiline expression | `cases/f012_multiline_expression/subject.gd` |
| F020 | If with both outcomes | `cases/f020_if_both_outcomes/subject.gd` |
| F021 | If without explicit else | `cases/f021_if_without_else/subject.gd` |
| F025 | For loop zero/one/many elements | `cases/f025_for_loop_iteration/subject.gd` |
| F022 | Elif chain (tier 1) | `cases/f022_elif_chain/subject.gd` |
| F023 | Nested decisions (tier 1) | `cases/f023_nested_decisions/subject.gd` |
| F024 | While loop zero/one/many iterations (tier 1) | `cases/f024_while_loop_iteration/subject.gd` |
| F026 | Break and continue (tier 1) | `cases/f026_break_continue/subject.gd` |
| F027 | Match and fallback (tier 1) | `cases/f027_match_fallback/subject.gd` |

F022 is tier 1, not tier 0, but lives here since it's pure GDScript with no
live-process/harness needs, matching this group. It's the first fixture
built using the 2026-09-19 branch-obligation schema fix (see
`pilot/harness/oracle.py`'s module docstring) from the start: decision
lines are now first-class `{"kind": "branch", "branch_type": ...}`
obligations expressing ground truth, independent of any tool's actual
behavior -- this is what let F020's gd-tools branch-counter deviation be
detected mechanically (a `false_hit` via `comparator.compare()`) instead of
needing hand-written prose. F020 and F021 were retrofitted with decision-line
obligations the same day for consistency.

Each `subject.gd` exposes a single static entry function, called directly by
`driver.gd` — no fixture is rewritten to suit a particular collector's
integration style, per the implementation plan's constraint.

Reproduce, using the pinned Godot 4.7.1 binary recorded in
[pilot-environment.md](../../docs/benchmarks/pilot-environment.md):

```sh
../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd
```

Expected: every case prints `PASS`, ending with
`All tier-0 group 1 fixtures match their behavioral specification.` and exit
code 0.

## Group 2 — live Godot process lifecycle (autoloads, await)

Autoload registration order is a project-wide setting, so F040 and F091 are
each their own self-contained mini Godot project (own `project.godot`) rather
than subdirectories of the shared `project.godot` above.

| ID | Case | Directory |
| --- | --- | --- |
| F040 | Autoload initialization, ordered before the collector autoload | `cases/f040_autoload_before_collector/` |
| F091 | Autoload initialization, ordered after the collector autoload | `cases/f091_autoload_after_collector/` |
| F045 | Await suspension and resumption | `cases/f045_await_resume/` |
| F060 | Deterministic state preservation across script reload | `cases/f060_reload_state/` |

F040/F091 use identical fixture scripts (`event_log.gd`, `user_autoload.gd`,
`collector_marker.gd`) with only the `[autoload]` order in `project.godot`
reversed between the two. `CollectorMarker` is a stand-in for a real
collector's own `_ready()`-activated autoload, not a real coverage tool.
Confirmed empirically on the pinned engine: reversing the order flips whether
the user autoload observes `collector_active=true` or `false` at its own
`_ready()` — a real fact about **Godot's own autoload ordering**. This is
*not* confirmed to be gd-tools' actual behavior: reading
`addons/gd-tools-coverage/coverage.gd` directly (see the 2026-09-19
corrections in `oracles/F040.json` and `oracles/F091.json`) shows gd-tools'
real counting only activates via GUT's pre-run hook, which fires after
Godot's entire autoload phase completes regardless of ordering — meaning
F040 and F091 likely converge to the *same* result for the real tool, not
the order-dependent difference this pair demonstrates for the engine alone.
A real gd-tools+GUT run against an autoload fixture, to check this, is
unbuilt BP05 work.

F060 isolates `Script.reload(true)` — the exact mechanism gd-tools 0.4.0 uses
to instrument an already-running autoload without discarding its instance —
from gd-tools' separate source-rewriting step, which this fixture does not
perform. Confirmed on Godot 4.7.1: `reload(true)` preserves both object
identity and mutated instance state; `driver_baseline.gd` (no reload) and
`driver_covered.gd` (calls `reload(true)` mid-run) both reach
`counter=111`.

Each has its own driver; run from inside its case directory:

```sh
cd cases/f040_autoload_before_collector && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd
cd cases/f091_autoload_after_collector  && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd
cd cases/f045_await_resume              && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd
cd cases/f060_reload_state              && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver_baseline.gd
cd cases/f060_reload_state              && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver_covered.gd
```

Autoload `_ready()` notifications are not delivered synchronously during
`SceneTree._initialize()` — group 2's drivers read logged state from
`_process()` on the first frame instead, not from `_initialize()`.

## Verify a fixture hasn't drifted from its bound oracle

```sh
sha256sum cases/f010_straight_line/subject.gd
# must match the "sha256" field in oracles/F010.json
```

## Group 3 — harness-dependent, real-tool findings

All five use `pilot/harness/`'s modules directly and, except F062, run the
*actual* pinned tools (gd-tools-cli 0.4.0, GUT v9.7.1) rather than modeling
them. Three produced real, reproducible defect findings, not synthetic ones:

| ID | Case | Directory | Real finding |
| --- | --- | --- | --- |
| F008 | Selected file cannot be instrumented | `cases/f008_cannot_be_instrumented/` | A UTF-8 BOM-prefixed `.gd` file is valid, runnable GDScript on Godot 4.7.1, but gd-tools' gdtoolkit-based parser rejects it and **silently drops it from the coverage plan** — no field anywhere in the plan/report schema records the omission, only a transient console warning. |
| F062 | Injected instrumentation failure | `cases/f062_injected_instrumentation_failure/` (uses F008 as its real-tool realization; check.py self-tests `pilot/harness/faults.py`'s generic fault injection) | Reuses F008's finding as its concrete case; check.py commits and reproduces the harness's own `make_unwritable` fault-injection primitive, for future tool-independent use. |
| F064 | Zero requested tests execute | `cases/f064_zero_requested_tests/` | Real GUT v9.7.1: correctly logs `[GUT ERROR]: Nothing was run.` and records `tests="0"` in JUnit XML output, but the **process exit code is still 0** — a CI pipeline gating on exit code alone would treat this as a passing build. |
| F065 | Graceful interrupted run | `cases/f065_graceful_interruption/` | Synthetic, tool-independent: proves the harness's marker-triggered SIGTERM (`pilot/harness/runner.py`) correctly interrupts a write-temp-then-rename report writer with no finished-looking artifact leaking. Establishes the termination contract real adapters should be checked against later. |
| F071 | Source revision mismatch | `cases/f071_merge_identity/` | Real gd-tools-cli 0.4.0: `coverage merge` sums hit counts purely by integer `file_id`. Its raw coverage-data JSON schema carries **no path or source hash at all** (confirmed from the tool's own docstring). Two sessions where file discovery order assigns the same `file_id` to two different files merge silently into one blended, meaningless count — exit code 0, no warning. |

Reproduce (each has its own driver/check script and, where noted, its own
mini Godot project):

```sh
# F008: engine ground truth
cd cases/f008_cannot_be_instrumented && ../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd

# F064: real GUT v9.7.1 (needs one-time --import per checkout to build the class cache)
cd cases/f064_zero_requested_tests
../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --import
../../../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit

# F062: harness fault-injection primitive (pure Python, stdlib only)
cd cases/f062_injected_instrumentation_failure && python3 check.py

# F065: harness marker-kill (pure Python, stdlib only)
cd cases/f065_graceful_interruption && python3 check.py

# F071: real gd-tools-cli 0.4.0 merge (pure Python; imports the gd-tools venv directly)
cd cases/f071_merge_identity && python3 check.py
```

## Status and open items

- All 16 oracles now share one schema (`pilot/harness/oracle.py`), replacing
  four incompatible `expected_hit` shapes that previously meant only F010
  could be compared mechanically. Validated against real BP04 evidence: F020's
  `union_obligations()` now mechanically reproduces a finding that previously
  needed hand-written prose. F008/F064/F065/F071 correctly keep their own
  shape -- they test process/artifact behavior, not line hits.
- An independent review agent performed a genuine second-reviewer pass on all
  16 oracles on 2026-09-19: re-hashed every referenced file, hand-traced every
  named input, re-ran every driver/check.py/compare.py, and read gd-tools/GUT
  source directly. 12 of 16 confirmed clean; 4 real issues found and fixed
  (F045 was missing an obligation; F060 and F065 had stale/inaccurate
  mechanism descriptions; F020 mischaracterized one comparison result). Each
  oracle's `reviewer` field now records specifically what was independently
  re-derived, per correctness-protocol.md's second-review requirement.
- All 16 tier-0 oracles (15 cases + F091) are now built (groups 1, 2, and 3).
- F008/F064/F071 constitute real, reproducible defect findings against the
  pinned tools, ahead of BP04's planned full adapter run — worth surfacing
  to the tool maintainers once independently reviewed, per the project's
  general policy of preferring upstream contribution over a new collector.
- F040/F091/F060 model gd-tools' architecture as read from source, not as
  measured by actually running gd-tools. Each oracle's `ambiguities` field
  says explicitly what BP04 needs to reconcile once the real adapter runs.
