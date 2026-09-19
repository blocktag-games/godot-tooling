# Godot Tooling

An open-source investigation into better tools for Godot development, beginning with trustworthy GDScript code coverage.

The project is in research and planning. This repository contains the ecosystem survey and a detailed benchmark protocol. A benchmark harness, coverage collector, test framework, and IDE plugin have not been implemented; no benchmark results have been measured here.

Our priorities are:

1. Code coverage: accurate execution measurements, useful reports, and dependable behavior on current Godot versions.
2. Live debugging: breakpoints, stepping, variables, stack traces, and a practical path from a failed test to a debug session.
3. IDE integration, especially PyCharm, including test execution and coverage visualization.
4. Profiling: understanding application and tooling costs, including how the benchmark and its profilers affect measurements.
5. Static analysis and a coherent development workflow as the project develops.

The initial research covers GDScript and Godot 4.7, with adjacent C# and native tooling included for comparison. Existing frameworks, coverage collectors, analyzers, and debugger protocols are candidates for reuse. The choice to extend an existing tool or create a new implementation remains open.

| Document | Purpose |
| --- | --- |
| [Session summary](docs/sessions/2026-09-06-project-kickoff.md) | Kickoff motivation, priorities, findings, and handoff context. |
| [Tooling survey](docs/research/2026-09-06-godot-tooling-survey.md) | Cited comparison of 31 projects/components and Godot's built-in facilities. |
| [Comparison inventory](docs/research/2026-09-06-godot-tooling-inventory.tsv) | Licenses, documented compatibility, releases, maintenance evidence, and adoption snapshots. |
| [Benchmarking methods survey](docs/research/2026-09-06-benchmarking-methods-survey.md) | How 14 testing, mutation, coverage, analysis, and benchmark systems measure performance. |
| [Application profiling guide](docs/profiling/application-profiling.md) | External resource/CPU measurements and Godot script, rendering, memory, and tracing workflows. |
| [Benchmark study plan](docs/benchmarks/README.md) | Research questions, correctness/performance/profiling protocols, catalogs, reproduction, and public reporting. |
| [Implementation plan](docs/benchmarks/implementation-plan.md) | Ordered benchmark work packages, first executable slice, completion evidence, and resource estimates. |
| [Pilot environment pin](docs/benchmarks/pilot-environment.md) | BP01: pinned engine binary/hash, machine record, gd-tools/GUT candidate pins, pilot schedule, explicit unavailable modes. |
| [BP04 adapter run](pilot/adapter-run/README.md) | First real gd-tools+GUT run: a clean match on one fixture, three confirmed findings on another, and a `reproduce.sh` verified to work from a clean checkout. |
| [Roadmap](docs/ROADMAP.md) | Project milestones and current status. |
| [GUT bugs to report upstream](docs/upstream/gut-bugs.md) | Twelve unfiled defects found reading `bitwes/Gut`'s source as an adapter candidate, tracked for a future small-PR contribution. |
| [Contributing](CONTRIBUTING.md) | How to contribute research, fixtures, reproducible results, and corrections. |

The survey and benchmark protocol draft are dated 6 September 2026. They distinguish documentation, selected source inspection, and proposed experiments from runtime verification. Coverage accuracy, performance, profiler overhead, and PyCharm compatibility still need practical evaluation.

The benchmark plan specifies 88 correctness/integration cases, 20 workloads, and 28 experiment families; most remain planned catalogs, not implemented tests. The 16-oracle tier-0 vertical slice and the first gd-tools+GUT adapter run are implemented under `pilot/` (see the pilot environment pin and BP04 adapter run rows above), with three confirmed findings against the real, pinned tools. An internal review found specific gaps against each package's stated completion evidence; BP01, BP03, and BP04 are now closed, and BP02 is substantially closed (one oracle schema replacing four incompatible ones, a committed check for every case), with a second-reviewer pass on individual oracles deliberately deferred rather than claimed -- see `docs/benchmarks/implementation-plan.md` for the exact, current state of each package. Compare gd-tools, Nano Coverage, and godot-code-coverage, with GdUnit4 Coverage as a separately scoped feature comparator.

The [methods addendum](docs/benchmarks/methods-addendum.md) incorporates lessons from the broader ecosystem and separates profiling an application from profiling the benchmark harness. A [local environment probe](docs/research/2026-09-06-profiling-environment-probe.json) records tool availability and engine help/hash checks; application captures and benchmark execution remain pending.

This project uses the [Apache License 2.0](LICENSE). Surveyed tools retain their own licenses.
