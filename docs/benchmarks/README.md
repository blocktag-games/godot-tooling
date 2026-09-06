# Godot tooling benchmark: study plan

Protocol draft 0.1, 6 September 2026. **Planning only: no benchmark implementation, measured results, or verified collector compatibility is included in this revision.** Numerical settings below are proposed experimental choices, to be calibrated in a labeled pilot and frozen before the main study.

The first public deliverable should be a reusable benchmark suite and an evidence-backed report about GDScript coverage. It can help users choose existing tools and help maintainers reproduce defects, even if the research concludes that a new collector is unnecessary. Profiling is a first-class investigation: measure application performance, explain collector costs, and test how the benchmark and its profilers affect their own measurements.

## Questions and deliverables

| ID | Research question | Required evidence |
| --- | --- | --- |
| RQ1 | Which execution facts does each collector measure accurately? | Independent expected results, original reports, normalized differences, and declared measurement boundaries. |
| RQ2 | Does instrumentation preserve application behavior and report incomplete collection honestly? | Baseline/covered behavior comparisons, injected failures, source restoration, and run completion records. |
| RQ3 | What does coverage cost in realistic development workflows? | Paired timings, resource measurements, scaling curves, and uncertainty for specific tool/engine/runner combinations. |
| RQ4 | Where does that cost arise? | Separate profiles of engine, scripts, collector, orchestration, and reporting, with phase and process attribution. |
| RQ5 | How much do the harness and profiler perturb the benchmark? | Controlled experiments with harness, coverage, and profiler settings; independent timing checks and observer interaction estimates. |
| RQ6 | Can developers reproduce the workflow across runners, IDEs, and machines? | Installation records, GUT/GdUnit4/manual execution, exact PyCharm builds, and independent reruns. |
| RQ7 | What should this project build or contribute? | Decision record linking demonstrated gaps to upstream fixes, reusable adapters, or a new collector. |

The public package comprises a versioned protocol, small readable correctness fixtures, deterministic performance workloads, tool adapters, raw observations, analysis code, and a report generated from those observations. This draft specifies those artifacts; it does not provide their executable implementation.

| Read next | Purpose |
| --- | --- |
| [Correctness protocol](correctness-protocol.md) | Independent truth, coverage semantics, behavior, failures, and scoring. |
| [Fixture catalog](fixture-catalog.tsv) | Individually identified correctness and integration cases, all currently planned. |
| [Performance protocol](performance-protocol.md) | Baselines, workloads, repeated measurements, statistical analysis, and validity. |
| [Workload catalog](workload-catalog.tsv) | Work amounts, calibration rules, behavioral checks, and intended metrics. |
| [Profiling protocol](profiling-protocol.md) | Profiling tools, harness diagnostics, observer experiments, and later evidence synthesis. |
| [Experiment matrix](experiment-matrix.tsv) | Bounded experiment families, dependencies, and eligibility conditions. |
| [Reproducibility contract](reproducibility.md) | Run identities, adapters, artifacts, result states, and machine records. |
| [Publication plan](publication-plan.md) | Public protocol, evidence release, charts, review, corrections, and decision criteria. |
| [Implementation plan](implementation-plan.md) | Ordered work packages, completion criteria, budgets, and unresolved decisions. |

## Scope and comparison units

Start with GDScript and the kickoff's reference engine, Godot 4.7.1. Pin the actual executable hash and build properties before execution. The reference version is a study choice, not a promise that all candidates support it. A fallback engine can diagnose incompatibility but creates a separately labeled result stratum.

Shortlist the following configurations from the dated [survey](../research/2026-09-06-godot-tooling-survey.md). These are documentary findings to verify in the implementation phase.

| Candidate ID | Configuration to investigate | Important boundary |
| --- | --- | --- |
| gd-tools | Released package with supported GUT workflow; pinned development revision as a separate follow-up if needed. | Verify startup scope, branch semantics, and instrumentation error reporting. |
| nano | Released source and, if needed, pinned development source; manual and supported GdUnit4 modes separately. | Build/install feasibility, disk versus memory instrumentation, and line measurement. |
| godot-code-coverage | Pinned Godot 4-capable revision with GUT and standalone scene modes. | Verify exact engine compatibility despite older README wording. |
| gdunit4-coverage | Public editor/runner/extension combination, if obtainable under its terms. | Partly closed implementation, matched patched engine, and documented public file limit; feature comparator. |

Treat a **tool + revision + engine binary + runner + collection mode + configuration** as the comparison unit. Shared source fixtures do not make different runners or engine builds equivalent. Show both each tool's user-facing workflow and, where available, matched components. Never rank raw GUT and GdUnit4 suite times as collector overhead.

Use five study lanes:

1. **Semantic correctness:** small programs with explicitly reviewed execution obligations. All collectors receive the same application sources and inputs where their contracts permit.
2. **Workflow performance:** headless test suites, standalone scenes, fresh project import, repeated launches, and report generation. Performance eligibility is decided per workload after behavior and measurement checks.
3. **Profiling and measurement validity:** diagnostic captures, harness calibration, and controlled overhead experiments on a smaller representative subset.
4. **Developer integration:** Godot editor, live debugger, PyCharm, report navigation, and source mapping. Interactive timing is separate from automated throughput.
5. **Portability and replication:** clean installations and correctness on additional operating systems, followed by performance replication on named hardware.

Linux is the initial planning assumption because the current working environment is Linux. Available benchmark hardware, controlled machine time, and Windows/macOS access remain unconfirmed. Do not treat this development session or shared CI as a controlled performance run.

C#, native C++ coverage, mutation testing, static analyzer accuracy, GPU profiling, mobile/web targets, and a new IDE plugin remain adjacent or later studies. Preserve extension points and relevant evidence, but they are not prerequisites for the first GDScript coverage report. Exported-game support is an explicit capability question; unsupported collectors remain visible.

## Hypotheses and decisions to freeze

The primary correctness claims are: reported hits agree with the stated contract; declared in-scope source is accounted for; measurement failure is distinguishable from zero execution; and deterministic application behavior survives instrumentation. A counterexample limits the relevant claim. Passing the corpus establishes agreement with these cases, not proof of correctness for all GDScript programs.

The primary performance estimand is covered/uninstrumented elapsed-time ratio for the same workload, engine, runner, and machine. The profiler study tests whether overhead depends on coverage or harness configuration. We do not assume either negligible overhead or a defect in any named project.

Before collecting main-study data, freeze tool pins, application inputs, oracle revision, eligible comparisons, metric definitions, repetition counts, randomization seeds, exclusions, analysis scripts, and public claim boundaries. Record amendments in a new protocol revision and distinguish exploratory results. The [implementation plan](implementation-plan.md) explains how pilot findings become that frozen protocol.

Do not collapse the study into a single winner score. Accuracy, supported scope, robustness, performance, installation, openness, and IDE integration answer different user needs. Project popularity is not a benchmark metric. The decision may be to improve an existing project and publish this corpus as an independent contribution.
