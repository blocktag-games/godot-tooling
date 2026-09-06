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
| [Benchmark study plan](docs/benchmarks/README.md) | Research questions, correctness/performance/profiling protocols, catalogs, reproduction, and public reporting. |
| [Implementation plan](docs/benchmarks/implementation-plan.md) | Ordered benchmark work packages, first executable slice, completion evidence, and resource estimates. |
| [Roadmap](docs/ROADMAP.md) | Project milestones and current status. |
| [Contributing](CONTRIBUTING.md) | How to contribute research, fixtures, reproducible results, and corrections. |

The survey and benchmark protocol draft are dated 6 September 2026. They distinguish documentation, selected source inspection, and proposed experiments from runtime verification. Coverage accuracy, performance, profiler overhead, and PyCharm compatibility still need practical evaluation.

The benchmark plan specifies 87 correctness/integration cases, 20 workloads, and 28 experiment families. These are planned catalogs, not implemented tests. Execution starts with a 12-case vertical slice and one adapter before expanding to the full study. Compare gd-tools, Nano Coverage, and godot-code-coverage, with GdUnit4 Coverage as a separately scoped feature comparator.

This project uses the [Apache License 2.0](LICENSE). Surveyed tools retain their own licenses.
