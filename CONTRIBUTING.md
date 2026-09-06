# Contributing

Godot Tooling is currently a research and evaluation project. Start with the [README](README.md), [session summary](docs/sessions/2026-09-06-project-kickoff.md), and [roadmap](docs/ROADMAP.md).

Useful contributions include correcting the survey, identifying relevant tools, documenting reproducible compatibility results, and designing coverage fixtures with independently known expected results.

For research changes:

- Cite the maintainer's repository, official documentation, license file, or release record.
- Include the observation date and distinguish released features from development-branch or roadmap features.
- Distinguish documented support, selected source inspection, and runtime verification.
- Identify component-specific licenses when a project combines open and closed components.
- Keep the survey and tab-separated inventory consistent.

For evaluation results, include exact source revisions and versions, operating system, setup steps, reproduction commands, expected results, actual results, and failures or unsupported cases. See the [roadmap](docs/ROADMAP.md) for the proposed evaluation criteria.

Keep dated findings reproducible when tools change. Add a new dated evaluation or correction note rather than silently presenting later results as part of the original survey.

Before submitting documentation, check local links, table structure, whitespace, and inventory consistency. This bootstrap does not yet have a project-specific build or test command.

The project uses [Apache License 2.0](LICENSE). Third-party projects discussed or evaluated retain their own license terms.
