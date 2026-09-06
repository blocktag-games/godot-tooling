# Profiling the application, collector, and benchmark

This is a proposed investigation, not a claim that any profiler has been installed or validated for this project. The study has two outputs: diagnostic explanations of costs and an experiment on measurement overhead. Headline coverage-performance results come from the unprofiled conditions in the [performance protocol](performance-protocol.md).

## Profile at the appropriate layer

| Layer | Candidate mechanism | What to investigate | Interpretation boundary |
| --- | --- | --- | --- |
| GDScript and engine frame activity | Godot built-in profiler, performance monitors, sparse custom phase markers. | Script hotspots, callback costs, frame/physics work, collector hooks. | Inclusive/self time and frame totals differ; debugger communication and monitoring have costs. |
| Native engine and GDExtension | Linux `perf stat`/`perf record`, symbols and call stacks. | Parser/reload work, VM dispatch, counter updates, allocation, locks, file I/O. | CPU samples need attribution; missing symbols, blocked time, permissions, and sampling loss limit conclusions. |
| Explicit engine/extension phases | A matched Godot build with Tracy and selected trace zones. | Cross-thread timing, startup, collection, flush, frame spikes. | Build changes, enabled instrumentation, capture connection, and trace transport are separate factors. |
| Python orchestration, where used | `cProfile` and optional py-spy; unprofiled microbenchmarks for hot helpers. | Process launch, polling, log handling, serialization, hashing, normalization, and report generation. | Python profiling does not reveal GDScript execution inside a child Godot process. |
| OS scheduling and I/O | Linux perf events; later Windows WPR/WPA and macOS Instruments. | CPU versus waiting, scheduling, storage, process-tree behavior. | Different OS tools and counters are separate measurement strata. |
| Visual/gameplay behavior | Godot visual/frame tools; later GPU-specific captures. | Frame pacing, renderer behavior, CPU/GPU interactions. | A CPU call tree or headless workload cannot establish GPU execution time. |

Godot documents that its built-in profiler is disabled by default because profiling is costly; it exposes inclusive and self measurements and does not currently profile C# scripts. This supports measuring observer effects rather than assuming the editor profiler is neutral. [Godot 4.7 profiler documentation](https://docs.godotengine.org/en/4.7/tutorials/scripting/debug/the_profiler.html)

Godot's Tracy integration requires a build configured for Tracy; its documentation also calls for compatible client/server versions and explains capture connection behavior. Pin engine source, compiler, build options, Tracy revision, symbols, and capture mode. Compare the same Tracy-enabled binary with collection inactive and active before attributing costs to recording. A stock-versus-Tracy build comparison measures a separate build effect. [Godot 4.7 Tracy documentation](https://docs.godotengine.org/en/4.7/engine_details/development/profiling/tracy.html)

Python's documentation cautions that profilers are for locating costs rather than benchmarking, because their overhead can distort comparisons. Use cProfile diagnostically; use unprofiled elapsed measurements to evaluate a proposed harness optimization. py-spy is a separate sampling candidate whose settings and native-stack support must be validated on the actual host. [Python profiling](https://docs.python.org/3/library/profile.html), [py-spy](https://github.com/benfred/py-spy)

Linux perf requires the appropriate kernel and access configuration; record permission failures and unavailable counters explicitly. Do not silently elevate or change host security settings. Check sample loss, call-stack quality, hardware-counter multiplexing, and child-process coverage before interpreting captures. [Perf tutorial](https://perfwiki.github.io/main/tutorial/), [Kernel perf access documentation](https://www.kernel.org/doc/html/latest/admin-guide/perf-security.html)

Windows WPR records ETW events for analysis in WPA. Instruments offers CPU profile call-tree analysis on Apple platforms. These are optional later diagnostic paths; exact versions, automation, symbols, and redistribution constraints need their own feasibility checks. They are not dependencies of the open benchmark core. [Microsoft WPR](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/windows-performance-recorder), [Apple call-tree analysis](https://developer.apple.com/documentation/xcode/analyzing-cpu-profiles-with-call-tree-views)

## Diagnostic questions and captures

Start with W01 empty launch, W03 branch-heavy work, and W11 the representative scene. Add W09 script loading or W13 offline reports when the observed cost suggests it. Use profiles to test concrete explanations:

- Does startup scale with the number of selected scripts, total source size, or the number actually loaded?
- Does runtime scale with executed instrumentation sites, branch activity, calls, threads, or report size?
- Is the collector allocating or synchronizing at each hit, and does cost rise under contention?
- Is time spent inside GDScript, native engine work, the runner, the collector, or the Python parent?
- Are tail delays associated with reload, flushing, report generation, scheduling, or storage?
- Does report normalization or logging become the largest cost once application work is short?

For every capture, save the exact configuration and a paired unprofiled run. Record instrumented build identity, capture start/stop, process/thread scope, sampling event and requested/achieved rate, stack-unwinding mode, symbol resolution, buffers, lost records, and file size. Preserve native capture files and an export that can be inspected without the original GUI where licensing and tooling permit.

Name trace zones using stable phases: discovery, parse/plan, instrument, import/reload, startup, fixture work, counter flush, serialize, normalize, render, and cleanup. Mark a phase unavailable if the provider cannot expose it. Adding provider trace zones creates an explicitly labeled diagnostic fork; do not present its timings as those of the unmodified release.

Sparse application markers should use a monotonic clock within their process. Python can use `perf_counter_ns()`; Godot has monotonic tick methods. Nanosecond units do not guarantee nanosecond accuracy. Keep clock domains explicit; cross-process timeline alignment requires a verified common clock or a recorded synchronization estimate. Never subtract unrelated process-relative timestamps. [Python clocks](https://docs.python.org/3/library/time.html), [Godot Time](https://docs.godotengine.org/en/4.7/classes/class_time.html)

## Calibrate the measurement system

Before attributing profiles to a collector, implement these controls:

| Control | What it reveals | Required check |
| --- | --- | --- |
| No-op child process | Launch, reaping, log plumbing, metadata and artifact overhead. | Correct exit and complete artifact lifecycle even when useful work is negligible. |
| Empty Godot fixture | Engine startup and runner cost without application workload. | Distinguish empty application from accidentally executing zero requested tests. |
| Fixed CPU-work fixture | Timing and hotspot sensitivity to a known work increase. | Verified output and separately measured duration change for 1x/2x/4x work. |
| Sleep/wait fixture | Whether wall time and CPU time are confused. | Waiting dominates wall duration without being called equivalent CPU work. |
| Bounded allocation fixture | Memory metric scope and sampled-peak limitations. | Known allocation lifecycle, retention interval, and release; no claim of byte-exact OS RSS. |
| Log-volume fixture | Pipe backpressure, buffering, disk writing, and parser costs. | Exact emitted/received byte counts, no deadlock or truncation. |
| Report-size fixture | Normalization/render scaling independently of game execution. | Immutable report corpus, known record counts, parser validation. |
| Sparse-marker/no-marker pair | Cost of phase timing and event buffering. | Same useful work/output and named difference in measurement machinery. |

Profile the harness itself while it runs no-op and real children. Separate its CPU work from time waiting for children. Measure polling frequency, process sampling, output capture strategy, validation, hashing, and postprocessing. Prevent unbounded buffering; validate log backpressure and timeout behavior with synthetic children before relying on the harness for Godot results.

Use an independent minimal process launcher or a pinned hyperfine invocation to cross-check complete-command elapsed measurements. Match shell use, working directory, environment, preparation, warmup, and command boundaries. Investigate disagreement instead of averaging the instruments. Hyperfine exposes warmup/preparation and shell controls, but its defaults do not define our coverage experiment. [Hyperfine documentation](https://github.com/sharkdp/hyperfine)

For Python-only helper performance, pyperf is a candidate because it distinguishes calibration, worker processes, warmups, and values. It does not replace Godot fixtures or the process-tree measurement contract. [pyperf benchmarking guidance](https://pyperf.readthedocs.io/en/latest/run_benchmark.html)

## Factorial observer experiment

The smallest complete design has eight conditions for each selected workload/collector/profiler combination:

| Factor | 0 | 1 |
| --- | --- | --- |
| H: harness | Minimal documented launcher with the same child command and required result capture. | Full benchmark orchestration and configured monitoring. |
| C: coverage | Matched coverage-disabled baseline. | Coverage enabled with the same source/input scope. |
| P: profiling | Profiler inactive, with matched binary and necessary infrastructure. | One named profiler/capture configuration active. |

H=0 still has a controller, clock, and output handling; it is not a zero-observer universe. Prepare equivalent workspaces outside the common child-runtime measurement boundary. Measure both the child's fixed-work interval and each controller's complete workflow interval. If full and minimal launchers cannot execute an equivalent provider command, that factorial cell is unavailable; compare the complete workflows descriptively instead.

Within a block, randomize the eight conditions while keeping engine, inputs, source scope, and work count fixed. Validate behavior and required coverage in each condition. Use one profiler at a time initially. For Tracy, define inactive versus active capture precisely and test whether disconnected capture buffers data; disconnected is not automatically inactive.

Let `Y[h,c,p]` be log elapsed time for a single matched block. At a fixed harness setting `h`, the coverage–profiler interaction is:

```text
I_CP(h) = (Y[h,1,1] - Y[h,1,0]) - (Y[h,0,1] - Y[h,0,0])
interaction_ratio(h) = exp(I_CP(h))
I_HCP = I_CP(1) - I_CP(0)
```

An interaction ratio of 1 means equal multiplicative profiler overhead with coverage on and off in that comparison. Values away from 1 suggest that profiling changes the estimated coverage effect. Summarize paired interactions by session and use the same declared uncertainty method as elapsed ratios. Report harness-only and profiler-only effects as well as interactions; an interval containing 1 does not establish absence of a meaningful effect.

Pilot two sessions of five eight-condition blocks on a small subset; use ten sessions of six blocks only for selected main-study interactions after feasibility and variance review. Avoid a Cartesian expansion across every tool, fixture, profiler, and platform. Requested sampling rates such as roughly 50/100/200 Hz are initial sensitivity candidates where supported, not guaranteed achievable settings. Record achieved rates and lost samples. Event-driven tracing uses its own event-volume controls.

A provisional investigation trigger is more than 5% estimated observer overhead on a work-dominated workload, substantial uncertainty relative to the coverage effect, a changed hotspot ordering, or changed behavioral/coverage results. This is a prioritization rule to freeze after the pilot, not proof that smaller effects are harmless or larger ones invalidate all uses. Very short jobs may require larger fixed work to become measurable; report that scaling choice.

Do not subtract one average harness or profiler cost from every benchmark. Overhead can depend on program behavior and interact with coverage. Keep raw observations, matched controls, and the scope of any correction model; publish sensitivity if a correction is later proposed.

## From self-measurement to a later meta-analysis

Profiling the benchmark and measuring its observer effects constitute a measurement-validity study. A formal meta-analysis would synthesize multiple sufficiently comparable studies, such as independent labs or future protocol releases. They are related but different outputs.

For later synthesis, predefine a search/submission cutoff, study inclusion rules, exact workload/metric comparability, and a deduplication scheme. Extract tool/engine revisions, machine characteristics, effect estimates, uncertainty, sample hierarchy, missing data, and author relationships. Repeated runs on one host are not independent studies. Multiple effects sharing a baseline are correlated and cannot be pooled as independent observations.

Begin with a structured evidence table and plots stratified by engine, workflow, machine, and protocol. Quantitative pooling is optional: it requires compatible estimands and a model accounting for study-level variation and dependent effects, ideally reviewed by someone with statistical expertise. Do not fit a random-effects model merely because many CSV rows exist. With sparse or incompatible studies, publish the differences and avoid a pooled number.

The first release can credibly publish the observer experiment and a replication template. A broader meta-analysis becomes a follow-up once independent comparable datasets exist.
