# Performance measurement protocol

Updated 2026-09-20: a BP07 pilot has been run (200 rows, exploratory, kept out of confirmatory estimates per this document's own rule) and BP08's harness-validation controls are in place; the controlled BP10 main study this document specifies has NOT been run. Consult the [workload catalog](workload-catalog.tsv) and [profiling protocol](profiling-protocol.md).

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

**Frozen mechanism 2026-09-20, closing a gap the BP07 pilot review found, pinned after a BP09 review found the first version left the choice open:** the BP07 pilot's scratch projects shared one OS-level Godot user-data directory (`~/.local/share/godot/app_userdata/<project name>/`, including its shader cache) across every candidate and condition, because every scratch project used the same `project.godot` `config/name`. This did not bias BP07's within-candidate B0-vs-C ratios (the shared warm cache is equally warm for every condition), but it is not the per-condition isolation this section already asks for, and it is a genuine cross-candidate confound the main study must not carry forward.

The pinned mechanism (verified against the pinned Godot 4.7.1 binary's own extension-API dump, not assumed): Godot's own `[application]` settings `config/use_custom_user_dir=true` and `config/custom_user_dir_name="<candidate>-<condition>"` (full setting paths `application/config/use_custom_user_dir` and `application/config/custom_user_dir_name`), written into each scratch project's `project.godot` per (candidate, condition) -- not a `config/name` override (which a naive fragment-concatenation onto the shared base `project.godot` would silently fail to apply correctly without also replacing rather than appending the `[application]` header) and not an `$HOME`/`$XDG_DATA_HOME` process-environment override (riskier here because gd-tools' Python CLI runs from its own venv and may itself consult `$HOME` for unrelated purposes). `use_custom_user_dir` is the mechanism Godot documents specifically for this purpose and does not touch `res://`-relative addon paths or gd-tools' own absolute-path result artifacts (`gd_tools/test_runner.py` writes `.gd-tools/results.xml` under the project root, independent of the user-data directory), so neither is put at risk by this choice.

Execution order can introduce bias. Systems research has demonstrated that apparently minor setup changes can alter conclusions; that motivates recorded setup and randomized condition order here. [Mytkowicz et al., ASPLOS 2009](https://sape.inf.usi.ch/publications/asplos09.html)

## Pilot, freeze, and repeat

The following numbers are planning defaults, not established sample-size requirements:

1. Run two pilot sessions with five randomized blocks each on W01, W03, W05, and W11. Establish valid behavior, practical workload lengths, startup dominance, variance, and available metrics. Aim for approximately 1–5 seconds of useful fixed work where calibration is allowed.
2. Choose fixed input sizes, warmup counts, timeouts, source scope, primary metrics, and repetition counts using pilot evidence. Keep pilot observations out of confirmatory estimates. If the pilot exposes a large observer effect or unstable baseline, fix or delimit it before freezing.
3. For each primary cell, initially budget ten measurement sessions with six matched blocks per session. Each block executes one fresh process per condition in a recorded random order. **Amended 2026-09-20, before any BP10 data was collected:** the original ≥3-calendar-day spread is dropped as excessive for a single dedicated development machine used by one person for this study alone -- there is no multi-user contention or shared-infrastructure drift to average out across days here. Sessions may run consecutively within one sitting, but each session boundary requires a concrete, actually-measurable quiescence check immediately before the next session starts: idle CPU utilization below a stated threshold (e.g. 5%) sustained for a stated duration (e.g. 60s), measured directly (`/proc/stat` or equivalent), not merely a rest interval assumed sufficient. This machine has no confirmed thermal telemetry (`upower` exposes battery state only, not temperatures), so thermal quiescence is NOT claimed or checked -- if temperature-driven throttling affects results, it will only surface as session-to-session drift, which the analysis section's existing time-order-plot inspection is relied on to catch and report as a limitation, not prevented in advance. This amendment does not relax the independence assumption the statistical analysis places on session means; it shifts the burden from "spread over days" to "verify actual, measured idle-CPU quiescence before each session," and consecutive same-day sessions are more exposed to undetected drift than a multi-day spread was.
4. Balance B0/B1/C ordering across blocks when all three exist. With two conditions, balance AB/BA. Keep identical inputs and configuration within a block. Shuffle cell order within sessions using a separate recorded seed. **Frozen concrete algorithm 2026-09-20** (the BP07 pilot's own per-block `random.Random(seed).shuffle()` deliberately did NOT implement this balance -- see `pilot/performance/run_pilot.py`'s own module comment scoping that decision to the pilot only -- so this is new specification, not a description of existing pilot code, and it must not be read back into the pilot's already-collected, already-valid data):
   - **Seed scoping (disambiguated after a BP09 review found the first version left this open):** each (candidate, workload) cell gets its OWN within-session block-order seed, per session, derived the same deterministic way `pilot/performance/run_pilot.py::session_seed()` already derives the pilot's per-cell seed (`sha256(f"{candidate}:{workload}:{session}")`, truncated to 4 bytes) but with a role tag appended so it cannot collide with the separate cross-cell seed below, e.g. `sha256(f"{candidate}:{workload}:{session}:block-order")`. Each cell's block-order permutation sequence is therefore independent of every other cell's -- two different cells are NOT forced to share one shuffled permutation order. Record every derived seed (block-order per cell, cross-cell below) in the output data, not just the inputs used to derive them.
   - **Three-condition candidates (gd-tools: B0/B1/C).** Precompute the 6 permutations of `(B0, B1, C)`. For a 6-block session, shuffle the ORDER of those 6 permutations using that cell's own block-order seed above and assign one permutation per block in that shuffled order -- every condition then appears in every ordinal position (1st/2nd/3rd) exactly twice per session by construction (verified: the 6 permutations' first elements are `{B0,B0,B1,B1,C,C}`, second `{B1,C,B0,C,B0,B1}`, third `{C,B1,C,B0,B1,B0}` -- each condition twice per position regardless of shuffle order), while which permutation lands in which block stays randomized and reproducible. This design assumes exactly 6 blocks per session (item 3's frozen default); if that default changes, a different subset/repeat rule must be chosen and documented before the main study runs -- do not silently truncate or repeat the permutation list without recording the choice.
   - **Two-condition candidates (Nano Coverage: B0/C).** Build the list `[AB, AB, AB, BA, BA, BA]` for a 6-block session (three of each), shuffle its order with that cell's own block-order seed, and assign one entry per block -- exact 3/3 AB/BA balance by construction, order randomized and reproducible.
   - **Cross-cell shuffle.** Within a session, generate the list of all primary (candidate, workload) cells eligible for that session (`docs/benchmarks/performance-eligible-cells.tsv`'s "yes" rows), and shuffle their execution order using ONE SEPARATE seed per session (e.g. `sha256(f"{session}:cross-cell")`), distinct from every cell's own block-order seed above -- so which cell runs first/last within a sitting is also randomized and reproducible, independent of each cell's internal block order.
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

Prespecified invalidity reasons include wrong binary/input, corrupted artifacts, incorrect behavioral output, incomplete required collection, broken measurement boundaries, unrelated measured-job overlap, and documented machine-state violations. Slow but otherwise valid runs remain in the data. Timeouts, crashes, and collector failures remain outcomes; do not average their truncated durations into successful completion times or silently drop them. **Concretized 2026-09-20:** retain every row in the raw dataset unconditionally (per-attempt, regardless of outcome), but EXCLUDE any row with a failed behavior check or a timeout from every descriptive statistic and every paired log-ratio observation used for the confirmatory estimate -- report its count and reasons separately instead. `pilot/performance/pilot_report.py` implements exactly this rule (a gap a BP08 review found and fixed: an earlier version fed every row into its statistics regardless of outcome, latent only because the BP07 pilot itself had zero failures).

An invalid block may be replaced under a frozen bounded retry policy, but retain every attempt and analyze whether failure is condition-dependent. Publish successful-run performance with failure counts and the selection limitation. If usable pairs are insufficient, label the estimate unavailable or exploratory. CI executes correctness and smoke checks; performance claims require the controlled protocol and recorded host.
