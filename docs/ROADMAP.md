# Godot Tooling roadmap

Trustworthy GDScript coverage is the first priority. Live debugging, PyCharm integration, and profiling are requested feature areas. The benchmark should also investigate its own measurement overhead and produce evidence suitable for public release.

| Milestone | Status | Deliverable |
| --- | --- | --- |
| 1. Survey the ecosystem | Complete: documentary research and selected source inspection | [Survey](research/2026-09-06-godot-tooling-survey.md) and [inventory](research/2026-09-06-godot-tooling-inventory.tsv). |
| 2. Evaluate coverage and measurement quality | BP01 closed. BP02–BP04 partial: 15-case tier-0 corpus built and one real adapter run complete with confirmed findings, but oracle review/schema and harness isolation gaps remain (see implementation-plan.md). BP05 onward (remaining candidates, full tier-1 corpus) pending. | Shared correctness corpus, controlled performance study, profiling/observer experiments, and reproducible public report. |
| 3. Verify PyCharm integration | Planned within benchmark integration lane; unverified | Reproducible launch/attach, selected-test debugging, and original-source navigation. |
| 4. Choose the contribution and architecture | Open, dependent on evidence | Decision to extend, integrate, or implement, with demonstrated requirements. |
| 5. Prepare a first tooling release | Unscoped | Compatibility policy, installation, examples, and release checks for a demonstrated need. |

The [benchmark study plan](benchmarks/README.md) now specifies research questions, measurement contracts, 88 correctness/integration cases, 20 workloads, 28 experiment families, reproducibility requirements, and a publication process. Its [implementation plan](benchmarks/implementation-plan.md) orders the work and estimates initial effort and machine time. Catalogs describe planned work; they are not executed test results.

A [survey of benchmarking methods](research/2026-09-06-benchmarking-methods-survey.md) now covers 14 testing, mutation, coverage, static-analysis, and benchmark systems, including pinned source inspection for ten repositories. The [methods addendum](benchmarks/methods-addendum.md) refines runner phases, cache/iteration states, work-count checks, and capture validation. The [application profiling guide](profiling/application-profiling.md) provides external and Godot-specific procedures; no game profile has yet been captured.

BP01 is closed. BP02–BP04 are **partial** — an internal review found specific unmet completion evidence in each (no second-reviewer pass on any oracle, no isolated-workspace/structured-outcome mechanism in the harness, no literal one-command reproduction in the adapter run) and, separately, one incorrect finding in BP04's original write-up that was corrected the same day. See [implementation-plan.md](benchmarks/implementation-plan.md) for the exact gaps per package. See the [pilot environment pin](benchmarks/pilot-environment.md) for the exact Godot 4.7.1 binary/hash, gd-tools-cli 0.4.0 pin, and GUT v9.7.1 pin; [pilot/fixtures/](../pilot/fixtures/) for the 15-case tier-0 corpus (three cases produced real, reproducible findings against the pinned tools before the adapter run even started); [pilot/harness/](../pilot/harness/) for the evidence harness; and the [BP04 adapter run](../pilot/adapter-run/README.md) for the first real `gd-tools test --coverage` run: a clean match on one fixture, plus three confirmed findings on another, the sharpest being that gd-tools' branch-coverage percentage can read 100% while a branch's body never executed (its `if_true` counter fires on every evaluation of the decision, not on the true outcome specifically). Before BP05/BP06 broaden to more candidates and cases, the oracle schema gap is worth closing first: BP02's four incompatible `expected_hit` shapes mean only one of sixteen built oracles can be compared mechanically today, and BP06 alone adds roughly 70 more cases. Keep GdUnit4 Coverage as an optional feature comparison with its exact patched binaries and public tracking limit recorded.

Use Godot 4.7.1 as the kickoff's reference engine, pinning the actual executable and build before running. Evaluate released and development versions separately. Linux is the initial performance-planning assumption; hardware access and additional operating systems remain to be established. The study must not imply compatibility from a version label alone.

Milestone 2 progresses through these evidence gates:

1. **Executable correctness slice:** independently specified truth, baseline behavior, native report, normalized comparison, and complete artifact identity.
2. **Candidate evaluation:** supported and unsupported cases, source population, branch semantics, initialization, asynchronous behavior, incomplete runs, merging, and restoration.
3. **Measurement pilot:** matched baselines, fixed-work workloads, useful timing/resource boundaries, harness calibration, and profiler feasibility.
4. **Frozen study:** pinned inputs/tools, randomized repeated schedule, analysis/exclusion rules, and explicit uncertainty assumptions.
5. **Public evidence release:** raw observations, rebuildable analysis/figures, scoped conclusions, failure accounting, and reproduction instructions.

Profiling covers the application, native engine/extensions, collector, harness, and report processing. The [observer experiment](benchmarks/profiling-protocol.md) varies harness, coverage, and profiler settings to investigate measurement interactions. A later meta-analysis depends on independent compatible studies; it is not a prerequisite for publishing the first measurement-validity study.

For PyCharm, investigate existing JetBrains Godot components and LSP4IJ with Godot's DAP service. Record the exact IDE edition/build and plugin versions. Demonstrate launch or attach, a verified breakpoint, stepping, variables, stack frames, and debugging a selected failing test. Evaluate coverage gutters and source mapping separately. A protocol or integration working in Rider does not establish PyCharm compatibility.

The architecture decision should compare upstream improvements, reusable adapters/packaging, and a new collector against accuracy, scope, installation, maintenance, performance, complete implementation openness, and IDE needs. Publishing the benchmark corpus is itself a useful open-source deliverable and may precede any new tooling implementation.

The first tooling release should solve a demonstrated problem with a small documented workflow. Scope and adoption goals remain open; the benchmark must be free to conclude that improving existing projects is the best contribution.
