# GDScript coverage tooling: an evidence-based evaluation

**Status: study release, single machine.** Everything below is a demonstrated result, an inference, or a proposed decision, labeled as such per this document's own outline. Report generated 2026-09-21 against artifacts committed the same date; every quoted number is rebuildable from the source cited beside it.

## 1. Questions, configurations, and headline results

This study asked whether existing GDScript coverage tools measure execution accurately, preserve application behavior, cost an acceptable amount at realistic workloads, and integrate with the Godot Editor's debugger — for Godot 4.7.1, and for the two tools that survived a compatibility screen: **gd-tools-cli 0.4.0** (via GUT v9.7.1) and **Nano Coverage** at commit `fce7a0ae` (via GdUnit4 v6.2.1's session hook). A third candidate, godot-code-coverage, is confirmed incompatible with 4.7.1 (a type-checking break, silent: tests still pass, no coverage file is ever written) and is excluded, not silently dropped — see `pilot/candidates/godot-code-coverage/PIN.md`.

Headline results, each demonstrated below with its own evidence:

- Both tools' branch/line accounting has real, reproducible gaps, not just rounding differences: gd-tools can report 100% branch coverage on a branch whose body never executed; both tools silently drop some accessor/pattern-label lines from tracking entirely.
- Both tools' instrumentation shifts the source line reported by runtime errors AND by the Godot Editor's own debugger, for the identical unmodified source file — an already-published finding for gd-tools (F057), newly confirmed for Nano Coverage too, and newly confirmed at the debugger-protocol level for both (F082).
- Coverage cost depends heavily on what the code does: negligible on an empty application, roughly 1.1x on signal-heavy gd-tools code, and 4x–12x on branch-heavy or scene-heavy workloads, for both tools, from a controlled 1200-run study (BP10).
- gd-tools' installed-but-inactive mode costs nothing measurable (within 0.4% of baseline in every measured cell).
- Neither tool's debugger integration is fully verified: automatic error-break line reporting is confirmed wrong (above); explicit breakpoint binding remains untested, honestly, because it could not be exercised without either a GUI session this project could not launch or a fuller debugger-protocol implementation than was in scope (F082).

## 2. Candidates, versions, and installation

| Candidate | Version/commit | Runner | Installation outcome |
| --- | --- | --- | --- |
| gd-tools-cli | 0.4.0, tag `v0.4.0`, commit `b5044c33` | GUT v9.7.1 | Installed via Pipenv, no issues, within budget. |
| Nano Coverage | `fce7a0ae` (2026-06-13, upstream's latest as of 2026-09-19) | GdUnit4 v6.2.1 session hook | Built from source with `scons` (no sudo needed) after working around a packaging bug in its own `.gdextension` naming; its documented headless/CI API crashes outside a full editor-plugin context — its GdUnit4 hook integration is the only mode this study uses. |
| godot-code-coverage | latest commit `3c92852d` | — | **Excluded**: confirmed incompatible with Godot 4.7.1 (silent failure — tests pass, exit 0, no coverage file). |

Full detail: `pilot/candidates/*/PIN.md`, `pilot-environment.md`.

## 3. Coverage obligations and a worked example

A coverage "obligation" here is a hand-derived, independently-reviewed statement of what a correct tool should report for a given input, checked against the tool's actual native output rather than trusted from the tool's own self-report. Worked example, from fixture F020 (`pilot/fixtures/cases/f020_if_true_false/`): an `if/else` branch run once with each outcome should report both arms reached; gd-tools' `if_true` counter instead fires on every *evaluation* of the condition, so a branch whose body never executes can still read as reached. Every fixture in the tier-0/tier-1 corpus follows this same pattern: independent oracle, real tool run, byte-level comparison, discrepancy recorded with root cause — not summarized as a pass/fail score. Full schema: `pilot/harness/oracle.py`; full corpus: `pilot/fixtures/`.

## 4. Compatibility, correctness, and behavioral preservation

From the full corpus sweep (`docs/benchmarks/corpus-run-2026-09-19.md`, 106 real invocations across 53 named oracle inputs against both candidates, plus BP02's independent second-reviewer pass on all 16 tier-0 oracles):

**gd-tools-cli 0.4.0 — 13/53 inputs affected, 4 root causes**, all contract-independent or clearly labeled contract-dependent:
1. A counter labeled `if_true`/`elif_true`/`loop_body` fires on every *evaluation* of the decision, not on the labeled outcome (contract-independent — a real mechanism defect, not a convention dispute).
2. `elif_true`/`match_case` (taken-only counters) cannot distinguish "never evaluated" from "evaluated and false" (contract-dependent — a different oracle convention could accept this).
3. Three declaration/header lines have no trackable point in gd-tools' plan at all (contract-dependent).
4. Ternary/conditional expressions have zero branch-level tracking (contract-independent).

**Nano Coverage (via GdUnit4) — 6/53 inputs affected, 3 root causes:**
1. An untaken-but-evaluated `elif` header line reports as completely unhit — independently convergent with gd-tools' finding 2, using a different mechanism.
2. Match-statement pattern label lines (`1:`, `2:`, `_:`) receive no LCOV record at all when not matched (contract-dependent).
3. Property getter/setter accessor bodies are entirely absent from coverage tracking (contract-independent).

Both known-answer control gates (deliberately planted right/wrong answers used to prove the sweep script itself can fail) passed on every run, in both sweeps — the absence of more findings is not a silently-broken checker.

**Behavioral preservation:** F064 (gd-tools/GUT exits 0 with zero tests actually run — a naive exit-code check cannot see this; this project's own harness was fixed the same way once, twice, when it made the identical mistake against its own pilot data, see `pilot/performance/README.md`'s postmortems), F080 (application-behavior parity between GUT and GdUnit4 as runners), F081 (instrumentation timing relative to autoload `_ready()`) are all fixture-built and passing against real tools. Full list: `docs/benchmarks/fixture-catalog.tsv`.

**Scope not swept:** Group 2 lifecycle fixtures beyond one spot-check (F042, matched exactly) are not run against either candidate — deferred, not assumed clean. This is a real, stated gap, not a silent one.

## 5. Performance: elapsed and resource effects

Full detail, methodology, and every number: [main-study-results.md](main-study-results.md) (the BP10 controlled study — 1200 runs, 10 sessions × 6 blocks, zero failures, machine quiescence and cache isolation verified per-session, schedule re-derived exactly from recorded seeds). Reproduced here as the headline table (in-process work time, the study's primary metric — excludes process/runner startup, which dilutes the ratio by up to 2x, see that report's own postmortem of its second pilot pass):

| Workload | gd-tools C/B0 | Nano Coverage C/B0 |
| --- | --- | --- |
| Branch-heavy logic (W03) | 12.4x [12.3, 12.5] | 9.7x [9.6, 9.8] |
| Signals/deferred dispatch (W05) | 1.06x [1.05, 1.06] | 3.0x [2.9, 3.0] |
| Representative scene app (W11) | 4.5x [4.5, 4.5] | 3.7x [3.7, 3.7] |

Compare tools by absolute added seconds on identical fixed work, not by percentage — the two runners have different fixed floors, so percentage rankings between tools are not meaningful (`main-study-results.md`'s own "Reading the results" section shows this concretely: gd-tools' smaller percentage on one workload corresponds to a *larger* absolute cost than Nano Coverage's larger percentage). gd-tools' installed-but-inactive (B1) mode is free: every B1/B0 ratio is within 0.4% of 1.0.

**Failure/exclusion accounting:** 0 of 1200 runs failed their behavior check or timed out; 0 rows excluded from the reported statistics. All coverage-active runs (480/480) produced the expected artifact.

## 6. Where the cost arises

Deeper phase attribution (BP08) is partial, not complete: `pilot/performance/harness_profile.py` profiled only the Python harness's own orchestration (negligible — confirmed by `cProfile`, essentially 100% of its own wall time is spent blocked in `Popen`/`communicate`, not doing CPU work), not the collectors' internal engine-side cost breakdown. Native `perf` was unavailable this session (not installed, `perf_event_paranoid=3`, no sudo); a Tracy-instrumented build was not built. `godot --profiling` was confirmed to thread through gd-tools' launcher via a `GODOT_BIN` wrapper with no vendored-code changes, but real profiler-active data collection was judged separate scope and not run — see `docs/benchmarks/pilot-observer-matrix.tsv`. This is a genuine, stated gap: the study establishes *that* coverage costs what it costs, with much weaker evidence for *why*, beyond the qualitative fact (Section 5) that cost tracks how branch-heavy the covered code is.

## 7. Harness and observer-effect validity

Per RQ5, the measurement instrument was validated before trusting it: `pilot/performance/harness_control/validate_harness_timing.py` recovers known-magnitude ground truth (a measurement floor, a known wait interval, monotonic CPU/memory scaling, complete log capture) through the actual timing primitive used everywhere else in this study; an independent external timer (`/usr/bin/time -v`) agrees with it within noise, with the (stated, not overclaimed) limit that both mechanisms share one blind spot — a fully stdio-detached grandchild process would be invisible to both, and this was demonstrated, not just asserted, in `independent_timing_check.py`'s own module docstring. The harness's own measurement overhead (the H factor of the H×C×P factorial) is not distinguishable from zero at ~0.6% resolution, consistent with the timing window structurally excluding all of the harness's own Python bookkeeping. Full observer-factor availability (P, the profiler factor) is recorded per candidate, not assumed uniform: see Section 6.

## 8. Debugger workflow

Per BP11 (`pilot/adapter-run/f082_debugger_error_line_accuracy/`): launch/attach to Godot's own remote debug protocol — the same protocol the Editor's Debugger panel and VS Code's `godot-tools` extension speak — works and was verified directly by reverse-engineering the wire format against the pinned binary (no third-party debugger library existed to reuse). The automatic pause-on-unhandled-error path, which requires no debugger-side configuration and is exactly what a developer watching the Debugger panel during covered tests would see, reports the SAME wrong, shifted line as raw stderr text for **both** candidates — a new finding for Nano Coverage, which had never been checked before (F082, extending F057).

**What remains genuinely unverified, stated plainly rather than assumed:** explicit breakpoint binding (does a developer's own `-b` or Editor-gutter breakpoint actually pause execution at the intended original-source statement under instrumentation). A minimal debug-protocol client built for this project could not activate a manual breakpoint in several attempts; real debugger clients evidently perform additional protocol configuration this project did not reverse-engineer, and a live Editor GUI session was not available (no `xdotool`/`scrot`/`import` installed, would need sudo not cached this session; the only display present is the user's own live interactive desktop, not appropriate to launch automated GUI tests against). VS Code's `godot-tools` extension itself is not installed in this environment and was not exercised — it remained the documented, optional secondary target per BP11's own scope, not pursued. Coverage navigation: confirmed directly that neither candidate provides in-Editor coverage gutter highlighting; both are external-report-only (HTML for gd-tools, LCOV for Nano Coverage).

## 9. Limitations, reproduction, and decision

**Limitations** (see also each cited document's own limitations section):

- Candidate selection: two viable candidates surveyed and evaluated exhaustively within this project's install-effort budget; a hypothetical fourth tool released after 2026-09-19 is not covered.
- Incompatible versions: godot-code-coverage excluded, not tested further, per a real reproducible break.
- Ambiguous line semantics: contract-dependent findings are labeled as such throughout; this study does not claim a single universal obligation convention.
- Runner differences: gd-tools runs headless, GdUnit4's runner opens a window; process-interval floors are not comparable across tools for this reason (work-time is the metric this study treats as primary specifically to reduce, not eliminate, this confound).
- Shared-machine noise and hardware/platform coverage: **one Linux workstation, one engine build, one sitting — a deliberate scope decision (BP12 formally descoped 2026-09-20, see `implementation-plan.md`'s BP12 row), not a resourcing gap awaiting resolution.** No pooling across machines is implied or attempted.
- Correlated observations: 10 sessions give df=9 per cell; intervals are per-cell, not simultaneous across the whole table, with no multiplicity correction applied. One cell (gd-tools W03) shows a small (~1.5%) time-order trend across the 3.65-hour sitting, stated in `main-study-results.md` rather than hidden.
- Debugger breakpoint binding: unverified, per Section 8 — a real, open gap, not paperwork.
- CPU time and memory were not measured; only wall-clock spans.

**Reproduction**: see `reproducibility.md` for the run-identity/manifest model and its own status note on what is built versus planned. Every number in Sections 4 and 5 was independently re-derived from committed raw data (not merely re-read from a prior report) as part of this document's own review pass — see the git history for the commits touching `pilot/performance/pilot_results.tsv`, `main_study_results.tsv`, and each fixture's own `check.py`, every one of which is directly re-runnable.

**Decision**: see [architecture-decision.md](architecture-decision.md) for the full weighing. Short version: neither candidate needs replacing outright; both have specific, fixable defects (Section 4, Section 8) worth an upstream report (see [maintainer-review-package.md](maintainer-review-package.md)); no requirement demonstrated here justifies building a new collector from scratch.
