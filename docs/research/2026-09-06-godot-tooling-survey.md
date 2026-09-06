# Godot development tooling survey — 6 September 2026

Import note: This research was prepared during the 6 September 2026 kickoff session in topdown-lab and copied into godot-tooling. Links to that project now use a fixed source revision; workspace wording was adjusted for this repository. The inventory and dated research findings were retained. See the [session summary](../sessions/2026-09-06-project-kickoff.md).

This survey supports a proposed open-source project whose first priority is **GDScript code coverage**, followed by **live debugging and IDE integration, especially PyCharm**. It examines 31 projects/components plus Godot's built-in facilities. The accompanying [inventory](2026-09-06-godot-tooling-inventory.tsv) records repository links, license scope, compatibility evidence, releases where checked, repository push dates, and GitHub star snapshots.

The evidence supports evaluating existing coverage implementations before choosing a new implementation. Testing, static analysis, debugging, and integrated command-line workflows already have substantial prior art. A potentially useful project would need a demonstrated advantage in coverage correctness, installation, compatibility, interoperability, or IDE workflow. That opportunity remains a hypothesis to test.

This is a documentary and selected-source-code survey. No third-party test suite, coverage collector, native extension, or IDE plug-in was executed for this report. “Supports” below means documented support unless explicitly identified as source inspection. Release tags, compatibility claims, development-branch features, and measured behavior are distinct kinds of evidence.

Searches covered coverage, test frameworks, mutation testing, static/semantic analysis, formatting, debuggers, editor integrations, and CI. Maintainer repositories, source files, release records, and official documentation support the findings. Searches also used older projects and adjacent C#/native tooling to avoid confusing those capabilities with GDScript support. This is a broad survey, not a claim that every repository or commercial product has been found.

Godot itself provides several foundations:

- Its GDScript analyzer and configurable warnings provide static checking, including warnings promoted to errors. External project-wide automation remains a separate concern. [Warning system](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/warning_system.html)
- Its debugger already supports inspecting a running game. Profiling reports performance information; that does not establish executable-line or branch coverage. [Debugger panel](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html), [Profiler](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/the_profiler.html)
- Its LSP and DAP services provide language and debugger integration through a running Godot instance. These are foundations for IDE work. They do not provide a coverage data protocol. [External editor integration](https://docs.godotengine.org/en/stable/tutorials/editor/external_editor.html)
- Its internal doctest/GDScript implementation tests serve engine development. The documentation explicitly distinguishes the GDScript implementation test runner from testing users' game scripts. [Engine unit testing](https://docs.godotengine.org/en/stable/engine_details/architecture/unit_testing.html)

**Coverage is the most relevant comparison.** All percentages and performance descriptions advertised by projects should be treated as claims until checked against known execution results.

| Project | Measurement and integration | Engine/source approach | License and maturity | Decision relevance |
| --- | --- | --- | --- | --- |
| [gd-tools](https://github.com/mansyar/gd-tools) | Advertises line and branch coverage; GUT integration; HTML, LCOV, Cobertura; unified test/lint/format CLI. | Python builds an instrumentation plan; GDScript injects counters and reloads scripts in memory. | v0.4.0 released 2026-07-15; package metadata marks beta and declares MIT. A standalone license file was not retrieved. | Closest existing project to an integrated coverage toolchain. Evaluate first. |
| [Nano Coverage](https://github.com/IgorBayerl/nano-coverage-godot) | Line coverage, LCOV, editor gutters, session merging, manual gameplay, and GdUnit4 hooks. GUT integration is listed as planned. | C++ GDExtension using Tree-sitter; disk instrumentation with backups for manual play, or memory instrumentation for test integrations. | Apache-2.0; README calls it alpha/developer preview and requires source builds. v0.1.1 release observed; main contains later work. | Strong candidate for an open coverage library/editor foundation. Exact Godot 4.7 compatibility and distribution need testing. |
| [GdUnit4 Coverage](https://github.com/godot-gdunit-labs/gdUnit4-coverage) | Advertises line, function, and branch coverage; editor visualization; LCOV. | Patched Godot “gdcov” runner plus GDExtension. README requires Godot 4.7 and GdUnit4 6.2+. | v0.1.4, open beta. Editor plug-in is MIT; engine patch and GDExtension are closed source. Public build stops tracking new files after 20 distinct files. | Relevant feature benchmark. The published source does not provide the full measurement implementation. |
| [godot-code-coverage](https://github.com/jamie-pate/godot-code-coverage) | Line coverage, GUT hooks, standalone scene execution, thresholds, JSON persistence and merging. | GDScript source instrumentation. | Repository declares MIT. README still says Godot 3.5, but main was upgraded to 4.4 and has later fixes. | Must remain on the shortlist; classifying it as exclusively Godot 3 would be misleading. Godot 4.7 is unverified. |
| [godot-coverage-hack](https://github.com/koalafr/godot-coverage-hack) | Matches source filenames to test filenames; emits pseudo-coverage reports. | No execution measurement. | MIT; repository last push observed in 2022. | Useful historical distinction: test-file presence is not code coverage. |

Selected source inspection changes how these candidates should be evaluated:

1. **gd-tools:** the collector calls `reload(true)`, restores the original source when reload fails, and records errors. Its architecture document describes activating counters at the test pre-run hook, after autoload initialization. Startup coverage and incomplete instrumentation therefore need explicit evaluation. These observations do not establish that its final report incorrectly succeeds; that requires an end-to-end failure test. [Collector source](https://github.com/mansyar/gd-tools/blob/main/src/gd_tools/addons/gd-tools-coverage/coverage.gd), [Architecture](https://github.com/mansyar/gd-tools/blob/main/docs/ARCHITECTURE.md), [License declaration](https://github.com/mansyar/gd-tools/blob/main/pyproject.toml)
2. **Nano Coverage:** the inspected LCOV writer emits line records and line totals. Branch measurement was not established from this writer or the README; do not infer it from the word “coverage.” Its standalone disk mode changes project files, which makes restoration and interrupted sessions important evaluation cases. [LCOV writer](https://github.com/IgorBayerl/nano-coverage-godot/blob/main/src/reporting/lcov_writer.cpp)
3. **godot-code-coverage:** commit `50f04102` explicitly upgrades to Godot 4.4; the current project file declares 4.4 features. A December 2025 commit addresses thread-safe collection. README compatibility is stale, while support for the latest engine is still unknown. [Upgrade commit](https://github.com/jamie-pate/godot-code-coverage/commit/50f04102bd01e382875e19e57aa5c7ef4a9ffd27), [Project configuration](https://github.com/jamie-pate/godot-code-coverage/blob/main/project.godot), [Commit history](https://github.com/jamie-pate/godot-code-coverage/commits/main/)

**Existing test frameworks provide useful integration targets.**

| Project | Current evidence | License | Implication |
| --- | --- | --- | --- |
| [GUT](https://github.com/bitwes/Gut) | v9.7.1 release; compatibility table lists Godot 4.7.x. GDScript assertions, doubles, parameterized tests, CLI/editor execution, and JUnit output. | MIT | A suitable first coverage adapter for the originating GDScript project. |
| [GdUnit4](https://github.com/godot-gdunit-labs/gdUnit4) | v6.2.1 release; table includes 4.7.1. Scene/input/signal testing, mocking, fuzzing, test reports, and CI integration. | MIT | A second major adapter target; substantial scene-testing functionality already exists. |
| [WAT](https://github.com/AlexDarigan/wat) | README explicitly says the repository is not Godot 4 compatible. Last repository push observed in 2023. | MIT | Historical prior art, not a current Godot 4.7 recommendation. |
| [gdmutant](https://github.com/kphutt/gdmutant) | Mutation testing through GUT, GdUnit4, or a custom command. README reports release verification on Godot 4.7.0 with named runner versions; provides HTML/JSON and a CI action. | MIT | A complementary way to assess whether assertions detect changed behavior. Its claimed verification was not reproduced here. |
| [GdUnit4Net](https://github.com/godot-gdunit-labs/gdUnit4Net) | C# framework with VSTest integration, selective engine-runtime use, and Roslyn validation of test attributes. | MIT | Mature integration concepts to study; separate from GDScript execution. |
| [GoDotTest](https://github.com/chickensoft-games/GoDotTest) | C# runner with CLI execution, coverage workflows, and VS Code test debugging. | MIT | Further evidence that the .NET tooling situation differs from GDScript. |

Advertised support for an engine version does not mean every engine/compiler edge case is resolved. A recent Godot issue reports an `await`/inheritance compiler problem affecting GUT. This is evidence for a regression corpus and version testing, not evidence that all current GUT testing is incompatible. [Godot issue 121584](https://github.com/godotengine/godot/issues/121584)

**Static analysis spans several different capabilities.** Style checks, syntax parsing, semantic/type analysis, and duplication detection should occupy separate cells in any product comparison.

| Project | Documented capability and current evidence | License | Reuse assessment |
| --- | --- | --- | --- |
| [gdtoolkit](https://github.com/Scony/godot-gdscript-toolkit) | Python/Lark parser, gdlint, gdformat, CLI/pre-commit integration. Latest release observed: 4.5.0, October 2025. | MIT | Established syntax/style tooling. Newer GDScript syntax needs checking; its release number alone does not prove engine incompatibility. |
| [gdstyle](https://github.com/atelico/gdstyle) | Rust lint/format/autofix tool, JSON output, editor plug-in and native/CLI backends. v0.2.5 observed; native integration requires Godot 4.6+. | MIT | Existing fast lint/format option; not evidence of complete semantic analysis. |
| [GDQuest GDScript Formatter](https://github.com/GDQuest/GDScript-formatter) | Tree-sitter-based formatter, style lint rules, CLI and editor integration. Release 0.24.0 observed. | MIT | Existing formatting and syntax infrastructure. |
| [GDShrapt](https://github.com/elamaunt/GDShrapt) | Standalone .NET semantic platform: type analysis, cross-file/scene resolution, refactoring and CLI. README distinguishes stable 5.x libraries from the 6.0 CLI alpha; LSP/editor products are described as planned/in development. | Apache-2.0 currently; versions through 5.0.0 were MIT. Future commercial layer described. | Serious semantic-analysis candidate. Avoid treating roadmap features as shipped. |
| [gdscript-analyzer](https://github.com/reactive-ui-toolkit/gdscript-analyzer) | Rust semantic library with CLI/LSP and native/Node/WASM consumers; scene-aware analysis. README says 0.5.x while current manifest contains 0.6.1 crates. | MIT OR Apache-2.0, confirmed in manifest. | Another semantic-analysis candidate. Exact release and engine-parity validation needed. |
| [graydwarf's GDScript Linter](https://github.com/graydwarf/godot-gdscript-linter) | GDScript quality checks and metrics, editor navigation, headless CLI; Godot 4.0+ claimed. | MIT | Useful existing editor/CI analysis tool; evaluate rule precision separately. |
| [tree-sitter-gdscript](https://github.com/PrestonKnopp/tree-sitter-gdscript) | Reusable GDScript grammar used by source tooling. | MIT | Candidate parsing substrate for coverage instrumentation; a syntax tree does not supply runtime behavior or semantic types. |
| [jscpd](https://github.com/kucherenko/jscpd) | Copy/paste detection; GDScript support appears in its changelog. | MIT | Existing duplication analysis. |

The analyzer's dual license and version discrepancy are visible in its [workspace manifest](https://github.com/reactive-ui-toolkit/gdscript-analyzer/blob/master/Cargo.toml). GDScript duplication support is documented in the [jscpd changelog](https://github.com/kucherenko/jscpd/blob/master/CHANGELOG.md).

**Live debugging and IDE integration already exist, with a specific PyCharm question still open.** For this survey, live debugging means launch/attach, breakpoints, stepping, stack frames, variables/watches, and useful game-state inspection. Coverage overlays and “debug this failed test” are additional integrations to evaluate.

| Integration | Existing capability | License scope | What remains to establish |
| --- | --- | --- | --- |
| [Godot Tools for VS Code](https://github.com/godotengine/godot-vscode-plugin) | Language services, debugging, breakpoints, stepping, watches, scene tree and inspector. | MIT extension | Coverage overlays/test navigation depend on additional tooling. Use as a working-design reference. |
| [GUT VS Code extension](https://github.com/bitwes/gut-extension) | Runs GUT tests from the editor, including individual test scopes. | MIT | Existing test UX; inspect exact versions and debugger interaction during evaluation. |
| [JetBrains Godot support](https://github.com/JetBrains/godot-support) | GDScript and .NET integration; Rider documentation covers debugging through DAP and game/scene tooling. | GDScript component MIT; shared/.NET components Apache-2.0. These licenses describe plug-ins, not the entire IDE. | PyCharm distribution, dependencies, and exact supported builds are not established by Rider documentation. |
| [LSP4IJ](https://github.com/redhat-developer/lsp4ij) | General LSP and DAP client for IntelliJ-family IDEs, with configurable adapters. | EPL-2.0 | Plausible PyCharm bridge. A working Godot/PyCharm configuration must be demonstrated. |
| [GDQuest Zed integration](https://github.com/GDQuest/zed-gdscript) | GDScript language support and launch/attach debugger configurations. | MIT | README records a Godot 4.4 debugging caveat. Exact 4.7 behavior is unverified. |
| [Emacs GDScript mode](https://github.com/godotengine/emacs-gdscript-mode) | GDScript editing; Godot 4 debugging through a separate DAP client such as dap-mode. | GitHub identifies GPL-3.0 | Illustrates reuse of protocols; its built-in older debugger is documented for Godot 3. |
| [nvim-dap](https://github.com/mfussenegger/nvim-dap) | Generic DAP client for Neovim. | GitHub identifies GPL-3.0 | Adapter configuration is additional work; a protocol client is not a coverage collector. |

JetBrains' README says other IDE SDKs can be targeted, but the current GDScript plug-in manifest declares shared Godot and platform DAP dependencies. It would be premature to promise that copying the Rider plug-in into PyCharm produces a supported integration. [Rider documentation](https://www.jetbrains.com/help/rider/Godot.html), [Plug-in manifest](https://github.com/JetBrains/godot-support/blob/master/gdscript/src/main/resources/META-INF/plugin.xml)

LSP4IJ offers an alternative integration route through its [DAP configuration](https://github.com/redhat-developer/lsp4ij/blob/main/docs/dap/UserGuide.md). The evaluation should cover the exact PyCharm edition/build, language plug-in compatibility, Godot process management, breakpoints, test launch, and source locations. Godot's DAP endpoint is distinct from its game remote-debug connection; the official example uses separate ports. [Godot protocol configuration](https://docs.godotengine.org/en/stable/tutorials/editor/external_editor.html)

**CI and adjacent ecosystems reduce the amount a new project would need to build.**

| Project/component | Contribution | Boundary |
| --- | --- | --- |
| [setup-godot](https://github.com/chickensoft-games/setup-godot) | MIT action installing Godot for macOS, Windows, and Linux headless runners. | Installation infrastructure; does not measure GDScript coverage. |
| [godot-ci](https://github.com/abarichello/godot-ci) | MIT Docker/export/CI templates. Docker image namespace is `barichello`; GitHub owner is `abarichello`. | Choose explicit engine image versions. |
| [gdUnit4-action](https://github.com/godot-gdunit-labs/gdUnit4-action) | MIT action for GDScript/C# tests and reporting. | Runner integration; pair compatible framework and engine versions. |
| [Coverlet](https://github.com/coverlet-coverage/coverlet) | MIT .NET coverage collector. | Managed-assembly coverage, not GDScript measurement. Godot-hosted C# execution requires its own validated setup. |
| [Godot regression-test-project](https://github.com/godotengine/regression-test-project) | MIT engine regression/visual fixtures; default branch observed as 3.x. | Historical/engine-specific prior art, not a general Godot 4.7 game testing framework. |

Native C++ coverage and ordinary .NET testing can be useful for GDExtension/C# components. They do not automatically measure scripts running in Godot's GDScript VM. Similarly, JUnit, LCOV, Cobertura, HTML, and JSON are report formats; their presence does not prove that the underlying measurements are accurate.

**The originating topdown-lab workspace supplies practical requirements.** Its [test gate](https://github.com/blocktag-games/topdown-lab/blob/766277080441f2b2dda72edfe5414ed27b89a2f1/tools/check.sh) contains import preparation, guards against zero executed tests, isolated user-data directories, and reversed test order. Its [strict analyzer wrapper](https://github.com/blocktag-games/topdown-lab/blob/766277080441f2b2dda72edfe5414ed27b89a2f1/tools/gdscript_strict_validate.py) automates Godot warnings with a baseline. Its [reference-coverage script](https://github.com/blocktag-games/topdown-lab/blob/766277080441f2b2dda72edfe5414ed27b89a2f1/tools/test_reference_coverage.py) explicitly measures a proxy rather than executed code. These are useful evaluation cases, not evidence that equivalent public features are absent. The script's broad statement that no maintained coverage tool exists should be re-evaluated against this survey; the existing file was not changed.

**Recommended decision process.** Keep the new project's identity provisional until the following comparison is complete:

1. Evaluate gd-tools, Nano Coverage, and godot-code-coverage against the same small GDScript project on Godot 4.7.1. Record the exact source commit, package, runner, and operating system. Test a released version and a development commit separately when their capabilities differ.
2. Include GdUnit4 Coverage as a feature/usability comparison, recording its patched-runner requirement and public tracking limit.
3. Use GUT and GdUnit4 suites that exercise identical application behavior. Add a manual-play session so coverage is evaluated independently of a particular test framework.
4. Produce expected-hit fixtures and compare reports mechanically. The first acceptance cases are listed below.
5. Test the smallest PyCharm integration using existing language/debugger components. Prove launch/attach and correct breakpoints before planning a new debugger engine.
6. Choose between contributing to an existing implementation, maintaining an adapter/distribution around it, or building a new collector. Choose a new collector only if the benchmark exposes requirements that existing designs cannot reasonably meet.

| Evaluation case | Required evidence |
| --- | --- |
| Unexecuted file and uncalled function | They remain in the declared denominator with zero hits, or a clearly documented exclusion. |
| Branch outcomes | Separate expected outcomes for if/else, if without else, match/default, early return, and short-circuit expressions; distinguish branch coverage from condition coverage. |
| GDScript language features | Correct handling of multiline expressions, lambdas, inheritance, static functions, properties, typed syntax, and preload/class_name relationships. |
| Startup and engine lifecycle | Define whether initialization, autoloads, _ready, signals, deferred calls, and process/physics callbacks are in scope, then verify their hits. |
| Await and re-entry | Correct source locations and outcomes across suspension and resumption. |
| Instrumentation failure | No successful “complete coverage” report when a selected file cannot be measured. |
| Empty, aborted, or crashed run | Completion state is explicit; stale reports cannot make an unsuccessful run pass. |
| Session merging | Source identity is checked; unrelated source revisions cannot silently share counters. |
| Behavioral preservation | Instrumented and ordinary runs produce the same expected application result. |
| Debugger source mapping | Breakpoints, stack traces, and report lines refer to the user's original source. |
| Files and user data | Temporary files/instrumentation are restored; tests do not depend on a developer's real saved profile. |
| Performance and installation | Record cold/warm execution time, memory, installation steps, and platform-specific builds against an uninstrumented baseline. |

These are proposed acceptance criteria, not reported defects in the surveyed tools. Coverage records execution; mutation testing assesses sensitivity to injected changes; neither alone proves correctness.

My present recommendation is to pursue **a well-tested, fully open coverage component that interoperates with established runners**, with IDE integration as a separately testable layer. Existing projects already attempt substantial parts of that product. A public compatibility/correctness corpus could be the first useful contribution while the implementation choice remains open.

A plausible project advantage would be demonstrated coverage accuracy, clear handling of incomplete measurements, straightforward installation, and one dependable path from an uncovered line to a test and a debugger. “Godot has no testing/static analysis/debugging” and “no coverage tool exists” are not defensible launch claims.

Repository popularity is a limited adoption signal. The inventory snapshot shows GUT and GdUnit4 with thousands/about a thousand stars, while several coverage tools have only a few. This suggests that existing runner users are a relevant audience; it does not establish demand for a particular new product or predict future stars.

The remaining unknowns are explicit: runtime coverage correctness, exact Godot 4.7 behavior for several collectors, supported OS/build distributions, debugger behavior with instrumented sources, PyCharm compatibility, and whether prospective users would adopt an improvement. The documentary survey is sufficient to shortlist tools; the shared benchmark is the next step before committing to a new framework architecture.
