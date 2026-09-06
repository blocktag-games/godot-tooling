# Godot Tooling

An open-source investigation into better tools for Godot development, beginning with trustworthy GDScript code coverage.

The project is in research and evaluation. This repository contains the initial survey and project direction; a coverage collector, test framework, and IDE plug-in have not been implemented.

Our priorities are:

1. Code coverage: accurate execution measurements, useful reports, and dependable behavior on current Godot versions.
2. Live debugging: breakpoints, stepping, variables, stack traces, and a practical path from a failed test to a debug session.
3. IDE integration, especially PyCharm, including test execution and coverage visualization.
4. Static analysis and a coherent development workflow as the project develops.

The initial research covers GDScript and Godot 4.7, with adjacent C# and native tooling included for comparison. Existing frameworks, coverage collectors, analyzers, and debugger protocols are candidates for reuse. The choice to extend an existing tool or create a new implementation remains open.

| Document | Purpose |
| --- | --- |
| [Session summary](docs/sessions/2026-09-06-project-kickoff.md) | Motivation, user priorities, findings, open decisions, and handoff context. |
| [Tooling survey](docs/research/2026-09-06-godot-tooling-survey.md) | Cited comparison of 31 projects/components and Godot's built-in facilities. |
| [Comparison inventory](docs/research/2026-09-06-godot-tooling-inventory.tsv) | Licenses, documented compatibility, releases, maintenance evidence, and adoption snapshots. |
| [Roadmap](docs/ROADMAP.md) | Proposed coverage and PyCharm evaluations and their completion criteria. |
| [Contributing](CONTRIBUTING.md) | How to contribute research, reproducible results, and corrections. |

The research is dated 6 September 2026. It distinguishes documentation and selected source inspection from runtime verification. Coverage accuracy and PyCharm compatibility still need practical evaluation.

The next proposed milestone compares gd-tools, Nano Coverage, and godot-code-coverage against the same expected-hit fixtures, with GdUnit4 Coverage as a feature comparison. See the [roadmap](docs/ROADMAP.md) for scope and evidence requirements.

This project uses the [Apache License 2.0](LICENSE). Surveyed tools retain their own licenses.
