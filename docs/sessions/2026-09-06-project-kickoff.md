# Project kickoff — 6 September 2026

This document summarizes the discussion that led to the godot-tooling repository and preserves the research handoff. It is a session summary, not a verbatim transcript.

The project began with an interest in creating an open-source Godot test framework that would help developers and attract community adoption. The initial concerns were compatibility of testing tools with recent Godot versions and the availability of coverage and static analysis. Those concerns were treated as questions to investigate.

The user identified **code coverage as the first priority** and added **live debugging and integration with IDEs such as PyCharm** to the feature list. The user then asked whether existing tools were open source and requested a more complete survey before choosing what to build.

The session produced two research artifacts:

| Artifact | Contents |
| --- | --- |
| [Godot tooling survey](../research/2026-09-06-godot-tooling-survey.md) | Comparison of 31 projects/components plus built-in Godot capabilities, including coverage, tests, mutation testing, analysis, debuggers, IDEs, CI, and adjacent .NET/native tooling. |
| [Tooling inventory](../research/2026-09-06-godot-tooling-inventory.tsv) | Structured evidence about licensing, documented compatibility, releases, repository activity, star counts, capabilities, and evaluation priority. |

The survey established several points that affect the project direction:

- GUT and GdUnit4 publish versions that list Godot 4.7 support. General incompatibility with recent Godot releases is not an adequate premise for a replacement framework.
- Coverage implementations already exist. The main candidates identified were gd-tools, Nano Coverage, godot-code-coverage, and GdUnit4 Coverage.
- Most surveyed projects have open-source licenses, but license scope matters. GdUnit4 Coverage documents an MIT editor plug-in with closed-source measurement components and a 20-file limit in its public build.
- Documentation may lag implementation. godot-code-coverage still describes Godot 3.5 support in its README, while its source history records a Godot 4.4 upgrade.
- Godot already has static analysis, a debugger, LSP, and DAP. Standalone analyzers, IDE integrations, and CI tooling provide additional foundations.
- Rider's documented Godot support does not establish PyCharm compatibility. Existing JetBrains components and LSP4IJ deserve a practical evaluation.
- Mutation testing is also represented by gdmutant. Execution coverage and sensitivity of assertions to changed behavior are different measurements.

The [survey](../research/2026-09-06-godot-tooling-survey.md) contains the primary-source links supporting these findings. Versions, licenses, and activity figures are observations from the survey date, not promises of current compatibility.

The research included web discovery, official documentation, repository metadata, releases, and selected source inspection. No third-party coverage collector, native extension, test suite, or IDE plug-in was executed. The original research documents passed document validation, local-link checks, table/TSV consistency checks, and inventory checks for 31 unique entries. Those checks validate the documents' structure, not the surveyed tools.

The original working context was the topdown-lab game project. Its custom test gate and analyzer wrapper supplied practical examples: fresh imports, detecting zero-test runs, isolating user data, varying test order, and distinguishing reference counts from execution coverage. The imported survey now links to a fixed source revision for those examples so it can be read independently of that checkout.

The user subsequently created the remote godot-tooling repository and requested a local clone, the session summary and produced documents, project files, and a push. The remote's initial commit selected Apache 2.0. This bootstrap retains that license and provides a README, roadmap, contribution guidance, and the research artifacts.

The following points are explicit user priorities:

| Priority | Status |
| --- | --- |
| Open-source project for the Godot community | Intended project direction. |
| Code coverage first | Confirmed. |
| Live debugging and IDE integration, especially PyCharm | Requested feature areas. |
| More complete survey before implementation decisions | Completed as documentary and selected-source research. |
| Community usefulness and adoption | Motivations; no numerical adoption target was set. |

The following remain recommendations or open decisions:

- Compare existing coverage tools using the same fixtures before choosing a collector architecture.
- Evaluate GUT and GdUnit4 adapters and a manual-play scenario.
- Explore a fully open coverage component and a public correctness/compatibility corpus as possible contributions.
- Choose whether to contribute upstream, build adapters and packaging, or implement a new collector after the evidence is available.
- Choose implementation language, supported platforms and engine versions, distribution method, and whether requiring a custom Godot build is acceptable.
- Verify the exact PyCharm build, edition, plug-in dependencies, debugger behavior, and coverage display.
- Establish runtime correctness and performance. No benchmark results are available yet.

The [roadmap](../ROADMAP.md) turns these recommendations into proposed, reviewable milestones. It does not imply that a new framework, collector, or IDE architecture has already been selected.
