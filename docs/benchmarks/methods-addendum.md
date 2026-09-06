# Benchmark methods addendum: framework research and application profiling

Draft addendum dated 6 September 2026. This records refinements prompted by the [14-project methods survey](../research/2026-09-06-benchmarking-methods-survey.md) and [application profiling guide](../profiling/application-profiling.md). The initial protocol has not been frozen or executed, so these are design changes made before observing study results.

The existing 87-case, 20-workload, 28-family catalogs remain planning inventories. This addendum refines how to implement them; it does not claim that extra executable fixtures or a benchmark harness now exist. Any additional workload rows need explicit IDs and a catalog update before scheduling.

## Requirements to incorporate before the pilot

| ID | Refinement | Existing work affected | Acceptance evidence |
| --- | --- | --- | --- |
| MA01 | Separate runner discovery, fixture setup, assertion work, application execution, and reporting wherever observable. | BP03/BP04/BP07; W01, W04, W13. | Named timing boundaries or explicit unavailability; overall process/workflow time retained. |
| MA02 | Distinguish fresh import, prepared launch, unchanged rerun, and source-edit rerun. | BP07; W09, W14. | Exact cache/source state and invalidation scope, with identical starting state across compared conditions. |
| MA03 | Pair performance with validated work counts and outputs. | BP02/BP04/BP06/BP07. | Requested/executed tests, selected/instrumented/reported source, expected obligations, and application behavior recorded. |
| MA04 | Keep default user workflow and equivalent-feature comparison as distinct views. | BP05/BP09. | Mode/runner/engine/configuration identities; no equivalence claim when scope differs. |
| MA05 | Add application-only profiling to the diagnostic path, independently of test runners and coverage. | BP08; W11; E15–E18. | Same standalone scenario captured externally and with a relevant Godot profiler, linked to an unprofiled baseline. |
| MA06 | Validate capture output, process ownership, symbol quality, and metric availability. | BP03/BP08. | Useful capture from the actual game; missing events/symbols/metrics explicit; help flags alone cannot pass. |
| MA07 | Separate quick regression guards from public effect estimation. | BP03/BP09/BP10. | CI detects functional/evidence failures; performance claims follow the frozen controlled schedule. |
| MA08 | Test measurement overhead at the level where it is introduced. | BP08; E08, E19–E21. | Child-runtime and complete-workflow controls; matched builds; observer interactions; no universal subtraction constant. |
| MA09 | Require public raw evidence for every published comparison. | BP09/BP13. | Complete attempts, settings, output checks, reproducible analysis, and accessible artifacts, including negative outcomes. |
| MA10 | Give mutation and analyzer comparisons their own work definitions if added later. | RQ7/future scope decision. | Operators, mutants, test selection, rules, files, semantic depth, cache state, and result preservation explicitly specified. |

These requirements draw on concrete precedents: Catch2's component/discovery benchmarks, Vitest's workflow/coverage timing, Coverage.py's configuration matrix, mypy's revision/cache comparison, StrykerJS's mutant-count check, mutmut's phase accounting, and Semgrep's findings checks. Their upstream methods and limitations are cited in the survey. Our publication protocol retains stronger session, uncertainty, and independent-oracle requirements where a consulted script supplies only a diagnostic check.

## Make the first application profile useful

Select one deterministic standalone scenario for W11. Establish its expected checkpoints and completed work without coverage or a test runner. First obtain external elapsed/resource observations. Then capture the scenario with the Godot script profiler; add the Visual Profiler only for rendering questions and native/OS tracing only when attribution remains unresolved.

Record startup/ready/scenario-complete/exit boundaries. An OS process interval and the scenario's own interval are both useful but have different scope. A 600-iteration cap is a smoke-capture bound, not a 10-second promise or a gameplay replay specification.

Use separate result dimensions for application correctness, capture quality, measurement scope, and performance eligibility. A profiler may successfully create a file while missing the game process or providing mostly unresolved frames. Treat these as capture-validation outcomes rather than successful hotspot evidence.

## Extend the observer experiment selectively

In addition to profiler on/off, capture configuration may matter: sampling frequency, stack-unwinding mode, buffer size, marker density, and event categories. Do not multiply them into the first full matrix. Use a small pilot to identify a question, then freeze a bounded experiment.

Godot's documented Android Perfetto categories provide a concrete later example: engine events alone versus engine plus script events. This belongs to a named Android/template stratum with matching controls. It is not a requirement to add Android to the first Linux coverage study.

BenchmarkDotNet's matched empty-method correction is a useful precedent for calibrating a measurement mechanism. Its correction model is not interchangeable with whole-process harness overhead or profiling interactions. Preserve the eight H/C/P conditions from the [profiling protocol](profiling-protocol.md) where equivalent commands can be executed.

## Mutation and static-analysis extensions

Do not bring these into the first coverage release merely because their benchmarking methods were surveyed. If selected later, define separate protocols:

- Mutation: generation, baseline tests, coverage/selection, mutant execution, and reporting; complete workflow time plus a precisely defined throughput denominator; valid/executed/skipped mutants and every terminal outcome; fresh versus incremental results.
- Static analysis: startup/import, parse, rule/type analysis, and reporting; rule set and semantic depth; selected/scanned/skipped files; cold, unchanged, and edited runs; expected diagnostics and failures/timeouts.

Within-tool revision comparisons can often hold work constant more closely than cross-tool rankings. For cross-tool comparisons, show capability and result differences alongside elapsed time. Different mutation operators or analyzer scopes must not be compressed into an unsupported universal speed ranking.

## Current evidence and next step

The [local environment probe](../research/2026-09-06-profiling-environment-probe.json) partially informs BP01/BP08: one engine executable and some command availability are known. It does not select a controlled machine, validate symbols, prove GPU profiling, or complete a scenario capture. No profiler installation or system-setting change was performed for this research.

Next implement BP01–BP04 as already planned, incorporating MA01–MA04 in the artifact and adapter contracts. Develop the first standalone application capture alongside BP07/BP08. Freeze the actual main-study schedule only after these paths produce correct, interpretable evidence.
