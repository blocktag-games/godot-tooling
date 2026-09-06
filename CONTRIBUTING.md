# Contributing

Godot Tooling is currently a research and planning project. Start with the [README](README.md), [roadmap](docs/ROADMAP.md), and [benchmark study plan](docs/benchmarks/README.md).

Useful contributions include correcting the survey, identifying relevant tools, reviewing coverage semantics, implementing fixtures with independently known expected results, and providing reproducible compatibility or measurement evidence.

For research changes:

- Cite the maintainer's repository, official documentation, license file, or release record.
- Include the observation date and distinguish released features from development-branch or roadmap features.
- Distinguish documented support, selected source inspection, proposed experiments, and runtime verification.
- Identify component-specific licenses when a project combines open and closed components.
- Keep the survey and tab-separated inventory consistent.

For benchmark contributions, use the [correctness protocol](docs/benchmarks/correctness-protocol.md), [performance protocol](docs/benchmarks/performance-protocol.md), and [artifact contract](docs/benchmarks/reproducibility.md). Bind expected results to original source hashes and explicit inputs. Do not generate the oracle from the collector being evaluated. Keep native reports, unsupported capabilities, incomplete runs, and behavioral differences visible.

Performance evidence needs exact configurations, matched baselines, fixed work, recorded order and repetitions, machine/session metadata, and a stated analysis. Profiling captures are diagnostic unless their observer effects are measured and the claim is explicitly scoped. Shared CI timing alone does not satisfy the planned public performance study.

The [catalogs](docs/benchmarks/README.md) currently contain planned cases and workloads. Adding a row does not implement or validate it. Actual results must carry source revisions, engine/tool/runner identities, setup and reproduction commands, expected/actual observations, and complete scheduled-attempt accounting.

Keep dated findings reproducible when tools change. Add a new dated evaluation or correction rather than silently presenting later observations as part of the original study. Follow the [publication plan](docs/benchmarks/publication-plan.md) for artifacts, limitations, corrections, and factual maintainer review.

Before submitting documentation, check local links, Markdown table structure, whitespace, TSV column counts/unique IDs, cross-references, and agreement between catalog counts and prose. This planning repository does not yet have a benchmark build or execution command; tested reproduction commands will be added with the implementation.

The project uses [Apache License 2.0](LICENSE). Third-party projects discussed or evaluated retain their own terms.
