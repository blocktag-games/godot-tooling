# Godot Tooling roadmap

The first priority is trustworthy GDScript coverage. Live debugging and PyCharm integration are requested feature areas. The milestones below are proposed next work; only the initial documentary survey is complete.

| Milestone | Status | Deliverable |
| --- | --- | --- |
| 1. Survey the ecosystem | Complete: documentary research and selected source inspection | [Survey](research/2026-09-06-godot-tooling-survey.md) and [inventory](research/2026-09-06-godot-tooling-inventory.tsv). |
| 2. Evaluate coverage implementations | Proposed | Shared fixtures, exact tool/version records, raw results, and a comparison. |
| 3. Verify PyCharm integration | Proposed | Reproducible launch/attach, test-debugging, and source-location demonstration. |
| 4. Choose the contribution and architecture | Open | Evidence-backed decision to extend, integrate, or implement. |
| 5. Prepare a first public release | Unscoped | Scope, compatibility policy, installation, examples, and release checks. |

For the coverage evaluation, start with Godot 4.7.1 as the session's reference version. Record the engine version and hash, tool release or commit, test-runner version, operating system, installation steps, and exact command for every result. Evaluate released and development versions separately where their features differ.

| Candidate | Evaluation purpose |
| --- | --- |
| gd-tools | Integrated CLI and GUT coverage implementation. |
| Nano Coverage | Open coverage component, editor UI, manual play, and GdUnit4 integration. |
| godot-code-coverage | Existing source instrumentation with a Godot 4 upgrade despite stale README compatibility text. |
| GdUnit4 Coverage | Feature/usability comparison, including its patched runner and public tracking limit. |

Use a small application with known behavior and equivalent GUT and GdUnit4 suites. Include manual gameplay where supported. Establish the expected measurements independently of each collector and retain the uninstrumented baseline.

The [survey's evaluation matrix](research/2026-09-06-godot-tooling-survey.md) defines the initial cases: unexecuted files, uncalled functions, branch outcomes, language constructs, initialization and callbacks, await/resumption, instrumentation errors, aborted or empty runs, source-aware merging, behavioral preservation, debugger source locations, user-data isolation, and performance.

The coverage milestone is complete when the candidate comparison records:

- Expected and actual executable-line and branch results for each supported case.
- Unsupported cases and incomplete measurements as explicit outcomes.
- Test behavior with and without instrumentation.
- Source changes, cleanup behavior, startup cost, run-time cost, and memory measurements.
- Reproduction commands, source identities, logs, and generated reports.
- A clear separation between upstream claims, observed results, and proposed improvements.

For PyCharm, first investigate existing JetBrains Godot components and LSP4IJ with Godot's DAP service. Record the exact IDE edition/build and plug-in versions. Demonstrate launch or attach, a verified breakpoint, stepping, variables, stack frames, and debugging a selected failing test. Evaluate coverage gutters and source mapping separately, especially when instrumentation changes line positions.

A reusable protocol or an integration working in Rider does not, by itself, complete the PyCharm milestone. Its deliverable is a configuration and demonstration that another developer can reproduce.

The architecture decision should compare three concrete options: contributing improvements to an existing project, supplying reusable adapters/packaging, or creating a new collector. Evaluate each against the benchmark results, license scope, engine compatibility, maintenance cost, installation, and IDE needs. Preserve unresolved questions rather than selecting a language or engine-fork strategy in advance.

The first release should solve a demonstrated problem with a small, documented workflow. Potential differentiators include accurate measurements, reliable handling of incomplete runs, easy installation, interoperability, and navigation from uncovered code to a test and debugger. Release scope and adoption goals remain open.
