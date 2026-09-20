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
| F029 | Conditional expression (tier 1) | `cases/f029_conditional_expression/subject.gd` |
| F030 | Short-circuit and/or (tier 1) | `cases/f030_short_circuit/subject.gd` |
| F011 | Blank, comments, and annotations (tier 1) | `cases/f011_blank_comments_annotations/subject.gd` |
| F013 | Multiple statements on one line (tier 1) | `cases/f013_multiple_statements_per_line/subject.gd` |
| F014 | Early return (tier 1) | `cases/f014_early_return/subject.gd` |
| F015 | Runtime error within an expression (tier 1) | `cases/f015_runtime_error_in_expression/subject.gd` |
| F016 | Repeated invocation (tier 1) | `cases/f016_repeated_invocation/subject.gd` |
| F032 | Static functions (tier 1) | `cases/f032_static_functions/subject.gd` |
| F033 | Lambda and Callable (tier 1) | `cases/f033_lambda_and_callable/subject.gd` |
| F034 | Inheritance and super (tier 1) | `cases/f034_inheritance_and_super/subject.gd` |
| F035 | Property getter and setter (tier 1) | `cases/f035_property_getter_setter/subject.gd` |
| F036 | Typed arrays, dictionaries, and signatures (tier 1) | `cases/f036_typed_collections_signatures/subject.gd` |
| F037 | Default arguments (tier 1) | `cases/f037_default_arguments/subject.gd` |

F032-F037 build out the `language` domain. F034 is the sharpest case: two
nested classes (`Base`, `Derived`) declare a same-named method, and
`Derived.greet()`'s `super.greet()` call reaches `Base`'s body without ever
calling it directly -- confirming hits attribute to the correct class body's
line, not to whichever class was instantiated at the top level. F033 shows
that creating a lambda literal and invoking it are distinct events (the
lambda body only hits when the Callable is actually called).

F011/F013-F016 open the `lines` domain (F012 was its tier-0 case). F013 and
F015 both use a runtime division-by-zero error (routed through a parameter,
not a literal, since a literal `100 / 0` is caught at parse time instead) to
force a "reached but not completed" case — the error aborts only the
`run()` call, the caller is unaffected, and GDScript coerces the aborted
call's return value to the declared type's default.

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
| F041 | Member and static initialization (tier 1) | `cases/f041_member_static_init/` |
| F042 | Enter-tree, ready, and exit-tree callbacks (tier 1) | `cases/f042_enter_ready_exit_tree/` |
| F043 | Process and physics callbacks (tier 1) | `cases/f043_process_physics_callbacks/` |
| F044 | Direct and deferred signals (tier 1) | `cases/f044_direct_deferred_signals/` |
| F046 | Await never resumes (tier 1) | `cases/f046_await_never_resumes/` |
| F048 | Deferred calls and queued deletion (tier 1) | `cases/f048_deferred_calls_queued_deletion/` |
| F049 | Load versus preload (tier 1) | `cases/f049_load_vs_preload/` |

F041 takes one CLI arg (`godot --headless --path . --script driver.gd -- <num_instances>`)
so each named input is its own fresh process, per the catalog's "fresh-process
initial state" requirement -- static-vs-instance initialization timing can't
be told apart from a single process's cumulative coverage report, only
across two genuinely separate runs (0 instances created vs. 3).

F044 similarly takes a CLI arg (`-- no_flush`) for its second input, which
quits before the frame that would flush a CONNECT_DEFERRED callback --
the only way to make "this callback never fired" a real fact in a
coverage report, since a report is always cumulative for its own process.
An earlier draft of both F041 and F044 tried to express this kind of
negative fact as a second snapshot within one shared process; that's
incoherent against any real report and was caught and restructured before
committing (see the 2026-09-19 note in oracles/F041.json).

F042's and F044's ordering claims (callback order; synchronous vs.
queued signal delivery) are carried by a log side-channel the driver
checks directly, not by the coverage obligations -- the obligation
schema can only express "this line was reached," never in what order,
same limitation already noted in F013's and F030's oracles.

F046 is F045's direct negative twin (resume_now never emitted, the
post-await continuation stays genuinely unreached); F048 uses the same
fresh-process-per-input rule as F041/F044 to make "queued work pending
at shutdown never ran" a real, checkable fact, not an intermediate
snapshot of a process that would later drain it. F049 completes tier-1
lifecycle (F040/F045/F091/F041-F044/F046/F048/F049); F047 is tier 2,
correctly deferred.

A corpus-wide lint pass while building this domain (checking that no
oracle obligation anchors to a blank/comment/signature line, and that
no if/while/for header reads unreached while a line in its body reads
reached in the same input) found and fixed one pre-existing violation
in F030 (two `func` signature-line obligations predating the
convention F032 established) -- see the 2026-09-19 note in
oracles/F030.json.

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

All six use `pilot/harness/`'s modules directly and, except F062/F065, run
the *actual* pinned tools (gd-tools-cli 0.4.0, GUT v9.7.1) rather than
modeling them. Three produced real, reproducible defect findings; one (F003)
is a real, verified **positive** result, not a defect:

| ID | Case | Directory | Real finding |
| --- | --- | --- | --- |
| F003 | Empty source population (tier 1) | `cases/f003_empty_population/` | Real gd-tools-cli 0.4.0: an empty selected population reports **0.0% coverage, not 100%** -- `reporter.py` explicitly guards the division (`... if total_lines > 0 else 0.0`), confirmed via both the Python API and the real terminal report renderer. A positive finding, recorded alongside the defects. |
| F004 | Include and exclude rules (tier 1) | `cases/f004_include_exclude/` | Real gd-tools-cli 0.4.0: default `addons/`/`tests/` exclusion correctly selects exactly the one application file from a three-file population. Another positive finding. |
| F005 | Loaded dependency outside selection (tier 1) | `pilot/adapter-run/f005_loaded_dependency_outside_selection/` (real end-to-end GUT+gd-tools run, not a standalone driver -- needs to observe a runtime effect) | Real gd-tools-cli 0.4.0 + GUT v9.7.1: calling excluded `vendor.gd` from selected `app.gd` neither crashes instrumentation nor broadens the plan -- `vendor.gd` never appears despite executing successfully, and `app.gd`'s own call site is correctly measured. A third positive finding. |
| F008 | Selected file cannot be instrumented | `cases/f008_cannot_be_instrumented/` | A UTF-8 BOM-prefixed `.gd` file is valid, runnable GDScript on Godot 4.7.1, but gd-tools' gdtoolkit-based parser rejects it and **silently drops it from the coverage plan** — no field anywhere in the plan/report schema records the omission, only a transient console warning. |
| F062 | Injected instrumentation failure | `cases/f062_injected_instrumentation_failure/` (uses F008 as its real-tool realization; check.py self-tests `pilot/harness/faults.py`'s generic fault injection) | Reuses F008's finding as its concrete case; check.py commits and reproduces the harness's own `make_unwritable` fault-injection primitive, for future tool-independent use. |
| F064 | Zero requested tests execute | `cases/f064_zero_requested_tests/` | Real GUT v9.7.1: correctly logs `[GUT ERROR]: Nothing was run.` and records `tests="0"` in JUnit XML output, but the **process exit code is still 0** — a CI pipeline gating on exit code alone would treat this as a passing build. |
| F065 | Graceful interrupted run | `cases/f065_graceful_interruption/` | Synthetic, tool-independent: proves the harness's marker-triggered SIGTERM (`pilot/harness/runner.py`) correctly interrupts a write-temp-then-rename report writer with no finished-looking artifact leaking. Establishes the termination contract real adapters should be checked against later. |
| F071 | Source revision mismatch | `cases/f071_merge_identity/` | Real gd-tools-cli 0.4.0: `coverage merge` sums hit counts purely by integer `file_id`. Its raw coverage-data JSON schema carries **no path or source hash at all** (confirmed from the tool's own docstring). Two sessions where file discovery order assigns the same `file_id` to two different files merge silently into one blended, meaningless count — exit code 0, no warning. |
| F061 | Baseline parse failure (tier 1) | `pilot/adapter-run/f061_baseline_parse_failure/` | Real gd-tools-cli 0.4.0 + GUT v9.7.1: an unparseable fixture is skipped from the coverage plan with an explicit named reason, the real engine parse error is preserved verbatim, and the run exits nonzero. A clean pass, correctly distinguishing a fixture defect from a collector defect. |
| F063 | Application test failure (tier 1) | `pilot/adapter-run/f063_application_test_failure/` | Real gd-tools-cli 0.4.0 + GUT v9.7.1: a genuine application bug that fails a correct assertion still yields fully accurate coverage for the code that executed — coverage completeness and test outcome are independent facts, confirmed directly. A related observation: F061's parse failure and this fixture's assertion failure share the SAME exit code (1), so exit code alone can't distinguish the two failure classes. |
| F068 | Truncated or malformed report (tier 1) | `pilot/adapter-run/f068_truncated_malformed_report/` | Real gd-tools-cli 0.4.0: a real coverage.json truncated in half is rejected explicitly by both `coverage show` and `coverage report` (exit 2, a specific "Invalid JSON" diagnostic naming the exact parse failure) — never silently read as zero or complete coverage. A clean pass. |
| F069 | Stale report from earlier run (tier 1) | `pilot/adapter-run/f069_stale_report/` | Real gd-tools-cli 0.4.0: **neither** `coverage show` nor `coverage report` checks the plan's own recorded `source_hash` against the current file on disk — a stale report from before a source change is presented as current with no warning at all, even though gd-tools computes and stores the hash. |
| F070 | Complementary run merge (tier 1) | `cases/f070_complementary_run_merge/` | Real gd-tools-cli 0.4.0: merging two disjoint-coverage runs against the same plan produces exactly the union of what each run touched. Confirms F071's summation-based merge policy coincides with set union when the two runs don't overlap. |
| F072 | Duplicate input merge (tier 1) | `cases/f072_duplicate_input_merge/` | Real gd-tools-cli 0.4.0: merging the identical coverage file with itself silently **doubles** the hit count, with no duplicate-input detection or warning of any kind — compounds with F069's finding for a CI retry/re-submission scenario. |
| F075 | Source restoration (tier 1) | `pilot/adapter-run/f075_source_restoration/` | Real gd-tools-cli 0.4.0 + GUT v9.7.1: subject.gd is byte-for-byte unchanged on disk after a mixed pass/fail run — a structural consequence of gd-tools' in-memory `Script.reload(true)` instrumentation, which never writes to the source file at all. |
| F076 | User-data isolation (tier 1) | `pilot/adapter-run/f076_user_data_isolation/` | Real gd-tools-cli 0.4.0 + GUT v9.7.1: two differently-named projects' test runs write to and read from completely separate `user://` profiles, with no leakage in either direction — inherited from Godot's own per-`config/name` user-data resolution. |
| F080 | GUT and GdUnit4 parity (tier 1) | `pilot/adapter-run/f080_gut_gdunit4_parity/` | Real GUT v9.7.1 + GdUnit4 v6.2.1: two thin test wrappers over byte-identical `subject.gd`, one per runner, produce a **byte-for-byte identical** event trace for the same inputs — the choice of test framework does not alter application behavior. Does **not** establish gd-tools coverage parity across runners (gd-tools' collection is bound to GUT's own hooks); see the oracle's ambiguities. |
| F081 | Standalone/manual driver (tier 1) | `pilot/adapter-run/f081_standalone_manual_driver/` | Real gd-tools-cli 0.4.0: a from-scratch manual driver — no GUT, no gd-tools CLI, just the raw `_GDTCoverage` autoload plus ~15 lines of hand-written glue replicating `pre_run_hook.gd`/`post_run_hook.gd` — produces coverage data **exactly equal** to the real GUT-path artifact. Found and fixed a real timing bug along the way: `_GDTCoverage`'s `_ready()` (where instrumentation happens) fires on the autoload's first idle frame, not synchronously before a driver script's `_initialize()`. |

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

# F061/F063/F068/F069/F075: real gd-tools-cli 0.4.0 + GUT v9.7.1 end-to-end runs
cd ../../adapter-run/f061_baseline_parse_failure && python3 check.py
cd ../f063_application_test_failure && python3 check.py
cd ../f068_truncated_malformed_report && python3 check.py
cd ../f069_stale_report && python3 check.py
cd ../f075_source_restoration && python3 check.py
cd ../f076_user_data_isolation && python3 check.py   # two sub-projects, own app_userdata each

# F070/F072: real gd-tools-cli 0.4.0 merge, hand-crafted coverage-data inputs
cd ../../fixtures/cases/f070_complementary_run_merge && python3 check.py
cd ../f072_duplicate_input_merge && python3 check.py

# F080: real GUT v9.7.1 + GdUnit4 v6.2.1, two sub-projects, own app_userdata each
cd ../../adapter-run/f080_gut_gdunit4_parity && python3 check.py

# F081: real gd-tools-cli 0.4.0, GUT reference + a from-scratch manual driver
cd ../f081_standalone_manual_driver && python3 check.py

# F066/F067: real gd-tools-cli 0.4.0 + GUT v9.7.1, real process signaling
# (each takes ~15-40s: a deliberately slow test gives a real window to
# find and kill the Godot process externally)
cd ../f066_forced_termination_crash && python3 check.py
cd ../f067_timeout_with_child_processes && python3 check.py
```

F061-F081's failures/merge/robustness/integration fixtures follow the
F005/F071 pattern throughout: real end-to-end `gd-tools test --coverage`
(or `coverage merge`) runs, never a reimplementation or a mock of the
tool's behavior.

| ID | Case | Directory | Real finding |
| --- | --- | --- | --- |
| F066 | Forced termination or crash (tier 1) | `pilot/adapter-run/f066_forced_termination_crash/` | Real gd-tools-cli 0.4.0 + GUT v9.7.1: a SIGKILL sent directly to the Godot process (simulating an OOM-kill, not a graceful interruption) leaves only the evidence written before the crash (`plan.json`) — `coverage.json`/`results.xml` are simply absent, never fabricated. gd-tools reports the real crash exit code (`-9`) to stderr. A fresh run afterward, with no manual cleanup, recovers and succeeds normally. |
| F067 | Timeout with child processes (tier 1) | `pilot/adapter-run/f067_timeout_with_child_processes/` | Found and fixed a real defect in **this project's own harness**: `pilot/harness/runner.run()`'s timeout used plain `subprocess.run(..., timeout=...)`, which only kills the direct child — the Godot process gd-tools spawns as its own child was left orphaned and running after the harness's timeout fired. Fixed via `start_new_session=True` + `os.killpg()` on timeout; verified with both a real gd-tools/Godot run and a new harness self-test (`pilot/harness/self_test.py`). |

Six of the eight failures/merge/robustness fixtures (F063, F068, F069,
F072, F075, F076) match their requirement or (F069, F072) surface a
genuine negative finding in gd-tools itself; F061/F063/F066/F068/F075/
F076 are clean passes. F067's finding is in this project's own harness
code, not a third-party tool -- fixed in the same commit as the
fixture that found it.

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
