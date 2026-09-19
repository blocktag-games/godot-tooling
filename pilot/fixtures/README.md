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
collector's own `_ready()`-activated autoload (modeled on gd-tools 0.4.0's
`addons/gd-tools-coverage/coverage.gd`), not a real coverage tool. Confirmed
empirically on the pinned engine: reversing the order flips whether the user
autoload observes `collector_active=true` or `false` at its own `_ready()` —
a real, order-dependent startup blind spot, not a hypothetical one.

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

## Status and open items

- Oracles are single-author, not yet second-reviewed (`"reviewer": null` in
  each oracle file). Per correctness-protocol.md, a second human review is
  desirable before public correctness claims.
- Group 3 (harness-dependent: F008, F062, F064, F065, F071) is not yet
  built — it needs BP03's orchestration harness first.
- No coverage adapter has run against these fixtures. That begins in BP04.
- F040/F091/F060 model gd-tools' architecture as read from source, not as
  measured by actually running gd-tools. Each oracle's `ambiguities` field
  says explicitly what BP04 needs to reconcile once the real adapter runs.
