# Performance measurement protocol

Draft settings for a future study; no timings have been collected. Consult the [workload catalog](workload-catalog.tsv) and [profiling protocol](profiling-protocol.md).

## Comparisons and baselines

For each supported tool/engine/runner/workload combination define:

| Condition | Meaning | Purpose |
| --- | --- | --- |
| B0 | Collector absent; application and runner otherwise matched. | User-facing cost relative to the ordinary workflow. |
| B1 | Collector installed/loaded but collection disabled, when such a mode actually exists. | Cost of installation, hooks, and inactive instrumentation. |
| C | Collection enabled in a recorded mode and source scope. | Total covered workflow cost and incremental collection cost. |

Report `C/B0`, `B1/B0`, and `C/B1` where available, with absolute times. Never synthesize a B1 mode by assuming that disabling report export disables collection. For workflows in which removing the plugin changes launch machinery, record that confound and describe the comparison as the complete workflow cost.

A patched engine requires its own coverage-disabled baseline on the same patched executable. A matched upstream build, built with comparable compiler/options, can estimate the combined patch/build effect. Without such controls, comparisons against an official binary measure the package as delivered; they cannot isolate collector overhead. Tracy builds similarly form separate binary strata.

The primary result set contains no attached profiler or debugger. A deterministic behavioral mismatch or incomplete required coverage makes the observation ineligible for an ordinary performance claim. Retain its elapsed time in a failure/diagnostic table. Do not declare a tool fast because it skipped work.

## Workloads and timing boundaries

Use both tiny diagnostic workloads and a modest representative scene application. The latter should contain state transitions, resource access, signals, asynchronous actions, and predictable outputs. A public real-project case study can follow once its revision, runnable scenario, assets, and redistribution terms are recorded. The originating topdown-lab project is a candidate, not a validated benchmark or a substitute for independent workloads.

| Metric | Start and end | Interpretation |
| --- | --- | --- |
| Clean installation | Begin documented local install/build steps to usable tool. | Friction and build cost; downloads/network reported separately from CPU benchmarking. |
| Fresh import | Start engine on a project without generated import state to completed import/exit. | Project-cache-cold setup cost. Does not mean cold operating-system caches. |
| Warm launch | Spawn a fresh process from prepared per-condition project state to application-ready marker. | Startup/compilation/instrumentation after import. |
| Workload interval | In-process monotonic start/end around a fixed unit of application work. | Runtime behavior; common markers are themselves measured overhead. |
| Process interval | Immediately before process creation to process exit/reaping. | Launch plus work plus in-process flush/teardown. |
| Tool workflow | Start tool invocation to validated raw report becoming available. | Developer wait time, including external collection and reporting required by that workflow. |
| Report processing | Start offline parse/normalize/render to files closed. | Analysis/report cost on immutable input, outside application execution. |
| Steady frame distribution | Predeclared measurement frames after fixed warmup. | Median and tail frame durations for a specified renderer/display mode. |

If a tool does not expose a phase boundary, mark that phase unavailable and retain the encompassing interval. External elapsed intervals can overlap in-process spans; do not add them as if they were disjoint. Report engine startup, fixture work, coverage flush, report rendering, and harness work only as separately measured spans.

Use fixed work counts for primary overhead tests. Calibrate an input size using uninstrumented pilots, then use exactly that size for every condition. A fixed-duration loop can silently perform less work under coverage; use it only for a separately defined throughput experiment, with completed work recorded. Record warmup work and whether coverage counters include it. If counters cannot be reset, validate the full invocation and label the runtime window separately.

Separate headless execution, editor execution, debug exports, and release exports. Record rendering backend, resolution, VSync, frame cap, physics tick rate, audio backend, and focus/background behavior when applicable. Headless measurements do not support claims about GPU frame cost or interactive frame pacing. Release exports are attempted only for supported configurations.

## Control the environment

Record CPU model/topology, affinity, RAM, storage/filesystem, OS/kernel, engine/build hashes, compiler where known, power source/profile, CPU governor/turbo state where visible, virtualization/container state, renderer/driver, background workload, and thermal telemetry if available. Do not claim a CPU was isolated, clocks fixed, or caches cold merely because a command requested it.

Run one measured application at a time on the designated machine. Suspend unrelated project jobs by arrangement; the harness must not kill arbitrary processes or silently change system power/security settings. Apply the same feasible controls to all conditions. A tuned-machine stratum and a normal developer-workstation stratum answer different questions and must remain separate.

Keep project and user-data caches isolated by condition while starting from equivalent prepared state. Record OS page-cache state as uncontrolled/warm unless a separate reproducible procedure establishes otherwise. Do not routinely flush global caches. Use fresh processes to expose launch variance; within-process iterations do not substitute for independent launches.

Execution order can introduce bias. Systems research has demonstrated that apparently minor setup changes can alter conclusions; that motivates recorded setup and randomized condition order here. [Mytkowicz et al., ASPLOS 2009](https://sape.inf.usi.ch/publications/asplos09.html)

## Pilot, freeze, and repeat

The following numbers are planning defaults, not established sample-size requirements:

1. Run two pilot sessions with five randomized blocks each on W01, W03, W05, and W11. Establish valid behavior, practical workload lengths, startup dominance, variance, and available metrics. Aim for approximately 1–5 seconds of useful fixed work where calibration is allowed.
2. Choose fixed input sizes, warmup counts, timeouts, source scope, primary metrics, and repetition counts using pilot evidence. Keep pilot observations out of confirmatory estimates. If the pilot exposes a large observer effect or unstable baseline, fix or delimit it before freezing.
3. For each primary cell, initially budget ten measurement sessions with six matched blocks per session. Each block executes one fresh process per condition in a recorded random order. Spread sessions across at least three days; define a session boundary and environmental checks in the frozen schedule.
4. Balance B0/B1/C ordering across blocks when all three exist. With two conditions, balance AB/BA. Keep identical inputs and configuration within a block. Shuffle cell order within sessions using a separate recorded seed.
5. Execute the frozen schedule and retain every attempt. Do not keep adding observations until an attractive ratio or significance level appears. Any extension creates a dated amendment and separate analysis.

Use pilot variation to decide where replication is needed: sessions, process launches, or within-process work. This follows the general rationale of allocating repetitions to the levels where uncertainty occurs; our specific schedule is a project choice, not a reproduction of the cited method. [Kalibera and Jones, ISMM 2013](https://kar.kent.ac.uk/33611/)

The seed schedule belongs to the workload and experiment, not the tool. All conditions in a block receive the same application seed. Keep the workload generator deterministic and versioned. For nondeterministic stress cases, record the allowed behavioral invariant and analyze failures separately.

## Statistical analysis

Predeclare the primary metrics as tool-workflow elapsed time and, for work-dominated workloads, in-process workload elapsed time. Primary comparisons are C/B0 for each named tool/workload stratum; C/B1 and resource measures are secondary. Keep all predeclared primary comparisons in the report.

For positive elapsed times, calculate the paired log ratio in block `b` of session `s`:

```text
d[s,b] = ln(time_C[s,b] / time_B0[s,b])
m[s]   = mean of d[s,b] within session s
R      = exp(mean of m[s] across sessions)
overhead_percent = 100 * (R - 1)
```

`R` estimates the geometric mean paired ratio with equal session weighting. It is not the ratio of arithmetic mean durations. Publish that definition, the raw paired values, absolute-time distributions, and per-session summaries.

The default uncertainty interval uses a two-sided 95% Student-t interval on the session means, transformed back with `exp`. Report session count, degrees of freedom, and the assumption that session means are sufficiently independent and approximately normal. Ten sessions still provide limited evidence. Inspect time-order plots and session variation; if drift or dependence undermines the assumption, report the limitation and avoid confident population claims. A session/block bootstrap can be a labeled sensitivity analysis, not a way to turn thousands of frames into thousands of independent experiments.

Frame p50/p95/p99 are calculated within each run, then summarized across independent runs/sessions. Choose frame counts in the pilot sufficient for the desired quantiles; do not publish p99 estimates from a few dozen frames. Retain timestamps or raw durations for tail analysis. Report throughput's units and ratio direction explicitly: higher throughput and lower elapsed time mean different things.

The main report estimates effects rather than declaring winners from p-values. The per-cell 95% intervals are not simultaneous family-wide guarantees. If making formal significance claims across many cells, freeze a family and multiplicity procedure, such as Holm adjustment, before the main analysis. Never infer equivalence from a non-significant difference. An equivalence claim needs an a priori practical margin and an appropriate interval/test.

Report each workload separately. An optional aggregate requires a predeclared common workload set, weights, and compatible coverage scope. Publish omissions; never let a tool improve its aggregate by failing a difficult case. Distinct machines, operating systems, runners, and engine builds do not form an interchangeable sample pool.

## Resources and invalid observations

Measure engine and harness CPU time separately where possible, plus complete workflow resource use. Define process-tree inclusion explicitly. For memory, use clearly named metrics: per-process peak RSS, sampled simultaneous RSS/PSS, or scoped cgroup peak charged memory. These measure different quantities. Summing each child's separate peak RSS does not measure the process tree's simultaneous peak, and shared pages can be counted repeatedly.

On an available Linux cgroup v2 setup, a fresh run cgroup's `memory.peak` includes its descendants; it is charged memory and may include file cache and kernel memory, not just application RSS. Record actual kernel/controller support and exact membership. Use a documented fallback metric when unavailable. [Kernel cgroup v2 documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

Record report/trace bytes, disk I/O, CPU samples/counters, and allocation counts only where the measuring mechanism and scope are established. An engine object counter is not an OS memory peak. Energy measurements require a defined sensor/device scope and separate controls; they remain optional.

Prespecified invalidity reasons include wrong binary/input, corrupted artifacts, incorrect behavioral output, incomplete required collection, broken measurement boundaries, unrelated measured-job overlap, and documented machine-state violations. Slow but otherwise valid runs remain in the data. Timeouts, crashes, and collector failures remain outcomes; do not average their truncated durations into successful completion times or silently drop them.

An invalid block may be replaced under a frozen bounded retry policy, but retain every attempt and analyze whether failure is condition-dependent. Publish successful-run performance with failure counts and the selection limitation. If usable pairs are insufficient, label the estimate unavailable or exploratory. CI executes correctness and smoke checks; performance claims require the controlled protocol and recorded host.
