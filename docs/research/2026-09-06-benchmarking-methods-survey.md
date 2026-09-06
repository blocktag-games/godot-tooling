# How testing and analysis tools benchmark themselves

Research snapshot: 6 September 2026. This survey examines **14 projects or benchmarking systems**, with selected repository files pinned for ten projects. The [inventory](2026-09-06-benchmarking-methods-inventory.tsv) distinguishes implementation inspection from maintainer documentation and records methods, limits, and source identities. No third-party benchmark was executed for this survey.

The useful precedent is a layered suite: measure the complete developer workflow, isolate expensive components, test scaling, and check that an optimization preserves the work and results. Projects differ considerably in statistical rigor. A published script, a regression threshold, a profiling helper, and a controlled comparative study are different kinds of evidence.

This extends the [Godot benchmark plan](../benchmarks/README.md). Profiling an actual game is covered separately in the [application profiling guide](../profiling/application-profiling.md).

## What was surveyed

Searches covered maintainer repositories, benchmark directories, contribution guides, performance workflows, and official profiling/measurement documentation. The selection includes testing, mutation, coverage, style/semantic analysis, and dedicated benchmarking libraries. It is a methodological sample, not an exhaustive ranking of every framework or a claim about unseen private infrastructure.

| Category | Projects | Main evidence |
| --- | --- | --- |
| Test frameworks/runners | pytest, Vitest, Catch2 | Profiling helpers; deterministic application matrices; assertion, discovery, and compilation benchmarks. |
| Mutation systems | StrykerJS, mutmut, PIT | End-to-end suites and component checks; controlled startup-delay experiments; documented selection and result semantics. |
| Coverage | Coverage.py's benchmark project | Projects × interpreter versions × coverage configurations, shuffled repetitions, logs, and saved observations. |
| Static analysis | Ruff, mypy, ESLint, Semgrep | Project and component benchmarks, cache/incremental modes, rule/configuration controls, result-preservation checks. |
| Benchmark infrastructure | pytest-benchmark, Google Benchmark, BenchmarkDotNet | Calibration, warmup, timing scopes, repetition, overhead controls, and structured output. |

A framework's facility for benchmarking user functions does not establish how its maintainers benchmark the framework itself. For example, pytest's own profiling helpers and the third-party pytest-benchmark fixture belong in separate rows. Google Benchmark is a microbenchmark library, not GoogleTest's unit-test runner.

## Test frameworks and runners

### pytest: profile collection and framework work directly

The pinned `bench/bench.py` invokes `pytest.cmdline.main` under cProfile and displays cumulative function costs. Its default target is an empty case; another supplied workload parameterizes two tests over 966 fixture values. These are useful diagnostic inputs, not a complete randomized performance study. [Profiling helper](https://github.com/pytest-dev/pytest/blob/431f3e1f5fd70b9b0f8afa2d20a10421542e5c6a/bench/bench.py), [Parameterized workload](https://github.com/pytest-dev/pytest/blob/431f3e1f5fd70b9b0f8afa2d20a10421542e5c6a/bench/manyparam.py)

A separate generator creates configurable nested directory/file trees for collection investigations. That isolates a factor which an ordinary application suite can hide: discovery topology and test-file count. [Collection generator](https://github.com/pytest-dev/pytest/blob/431f3e1f5fd70b9b0f8afa2d20a10421542e5c6a/testing/example_scripts/perf_examples/collect_stats/generate_folders.py)

**Godot application:** profile runner discovery, fixture construction, assertion dispatch, and test reporting independently of game logic. Vary directory shape, script count, and parameterized-test count. Keep diagnostic profiling separate from unprofiled performance comparisons.

### Vitest: realistic shapes, explicit configuration, and total wall time

The benchmark repository generates deterministic applications and supplies curated quick/default/full matrices. Factors include worker pools, isolation, environment, filesystem caches, and browser execution. Its documented default is three timed repetitions with a median. Cold/warm refer to specified tool caches, not a guarantee that operating-system caches are cold. [Benchmark design](https://github.com/vitest-dev/benchmarks/blob/c2a8bc1afce98fc5f5d145308ef4f6fde52b8188/README.md)

Its coverage driver compares no coverage, V8, and Istanbul on a selected warm configuration. It records whole-process elapsed time separately from the runner's displayed duration and coverage-generation time, retains samples, and records failed cells. Inspection shows an untimed priming run followed by consecutive repetitions for each cell. That is useful implementation evidence; it does not establish independent-session uncertainty or randomized cross-condition blocks. [Coverage driver](https://github.com/vitest-dev/benchmarks/blob/c2a8bc1afce98fc5f5d145308ef4f6fde52b8188/scripts/bench-coverage.mjs)

**Godot application:** preserve both process/workflow time and fixture time; include runner and collection modes explicitly. Use a curated matrix before a full cross product. Add our planned randomization and session accounting rather than copying a three-run median as sufficient publication evidence.

### Catch2: assertion paths, discovery scaling, and compilation

Catch2 separates fast/slow assertion paths, assertion types, optional stringification, and Debug/Release configurations. Its guide uses hyperfine for old/new comparisons and distinguishes formatting overhead from writing output. Compilation is also a developer-facing cost. [Maintainer benchmark guide](https://github.com/catchorg/Catch2/blob/897d8043eb192d0fc361c6339ce13e1cabe481c4/benchmarks/readme.md)

The discovery benchmark invokes the real CMake discovery implementation through a synthetic listing shim. The inspected script spans 1–16,000 tests with five repetitions and checks the generated registration count. This is a strong example of a synthetic workload testing a real integration boundary. [Discovery script](https://github.com/catchorg/Catch2/blob/897d8043eb192d0fc361c6339ce13e1cabe481c4/benchmarks/discover_tests/benchmark_discovery.py)

**Godot application:** measure startup/import/reload, discovery, passing assertions, failing assertion formatting, and report emission separately. Use unusually large inputs to expose scaling, while clearly labeling them as stress cases rather than typical projects.

## Mutation testing

### StrykerJS: realistic projects plus a guarded instrumentation microbenchmark

StrykerJS's experimental performance suite includes multiple projects and submodule-backed inputs. Its inspected launcher times individual projects and the overall suite. The checked workflow is manually dispatched and uploads mutation reports; this alone does not establish a continuously enforced statistical regression gate. [Suite description](https://github.com/stryker-mutator/stryker-js/blob/f9225709e9d13f4568201e9be8fe7809a3271778/perf/README.md), [Launcher](https://github.com/stryker-mutator/stryker-js/blob/f9225709e9d13f4568201e9be8fe7809a3271778/perf/tasks/run-perf-tests.js), [Workflow](https://github.com/stryker-mutator/stryker-js/blob/f9225709e9d13f4568201e9be8fe7809a3271778/.github/workflows/performance.yml)

The instrumenter tests measure one instrumentation call and assert both duration and expected mutant count. The large input expects 948 mutants; its configured time limit differs on Windows. This couples a performance guard with an output-volume check. These machine-sensitive thresholds are regression checks, not portable speed comparisons or evidence that the resulting mutants are all semantically valid. [Instrumenter performance tests](https://github.com/stryker-mutator/stryker-js/blob/f9225709e9d13f4568201e9be8fe7809a3271778/packages/instrumenter/test/perf/instrumenter.perf.spec.ts)

**Godot application:** verify the number and identity of selected/instrumented obligations while measuring instrumentation. A fast pass which drops scripts or probes must not become a performance improvement. Keep simple CI tripwires distinct from the controlled study.

### mutmut: isolate import, setup, and per-test costs

The `benchmark_1k` project supplies a synthetic 1,000-mutant workload and configurable import, conftest, and test delays to compare process/warmup strategies. Its README also records outcome distribution. The published speedups are upstream observations, not reproduced findings here. [Workload design](https://github.com/boxed/mutmut/blob/2f39c84dcbf3b9fdabafe395200d090d4f47de65/e2e_projects/benchmark_1k/README.md)

The driver records complete-command elapsed time, phase timings, mutant outcomes, and throughput defined using the mutation-testing phase. It preserves each configuration's artifacts. The inspected loop runs each strategy once per delay configuration; it does not itself provide repeated randomized blocks or confidence intervals. Its throughput denominator is therefore particularly important when comparing the reported number with end-to-end elapsed time. [Driver](https://github.com/boxed/mutmut/blob/2f39c84dcbf3b9fdabafe395200d090d4f47de65/e2e_projects/benchmark_1k/run_benchmark.py)

**Godot application:** vary import/reload and fixture-setup costs independently of useful test work. Distinguish generation, baseline execution, coverage collection, selected-test execution, and reporting. Add repeated blocks and record the random seeds for any synthetic jitter.

### PIT: selection and outcomes constrain a fair benchmark

PIT documents collecting line coverage and test timings before choosing tests targeted at a mutation. It distinguishes killed, survived, uncovered, nonviable, timeout, memory-error, and run-error outcomes. This is evidence about the workload and result semantics, not a standalone public benchmark harness verified by this survey. [PIT concepts](https://pitest.org/quickstart/basic_concepts/)

**Godot application:** mutation speed is not just elapsed time or mutation score. Record operator set, candidate count, valid/executed mutants, selected tests, early stopping, timeouts, incremental reuse, and final outcomes. Different mutation operators and selection strategies mean different work.

## Coverage instrumentation

### Coverage.py: matrix, shuffled repetitions, and persistent raw timings

The coverage benchmark implementation crosses projects, Python versions, and coverage configurations. It prepares environments outside the returned test duration, shuffles repeated combinations, saves raw durations to JSON, and summarizes medians and variability. It supports a no-coverage configuration and separate line/branch scenarios through project adapters. [Benchmark implementation](https://github.com/coveragepy/benchmark/blob/1309d521eaea4fb73131509d824d53f1d0b9afdf/benchmark.py)

**Godot application:** this is a close architectural precedent for our thin adapters and matched runs. Adopt recorded configuration matrices and persistent observations. Audit individual adapters and failure semantics rather than assuming every supplied project works: the inspected file includes disabled adapters and unavailable-baseline paths. Our schema should keep unavailable data explicit, retain session/attempt identity, and prevent cached observations from unrelated study conditions being silently reused.

## Static analysis

### Ruff: realistic macrobenchmarks, component microbenchmarks, and profiles

Ruff's contribution guide uses CPython as a large corpus, distinguishes cache-enabled/disabled command runs, and uses Criterion for linter/formatter microbenchmarks on individual files. It documents saved baselines and native profiling separately. [Contribution guide](https://github.com/astral-sh/ruff/blob/0587598dec85f558082dddada4017dcbac8efe79/CONTRIBUTING.md)

**Godot application:** combine real source corpora with focused parse, instrument, reload, and report workloads. Explicitly define the rule set and analysis depth when comparing analyzers: formatting, syntactic linting, and project-wide type analysis do different jobs. A faster analyzer running fewer rules is not an equivalent-work comparison.

### mypy: compiled artifacts, randomized revision order, and incremental edits

The inspected comparison script builds mypyc-compiled revisions, performs an unrecorded warmup, then randomizes revision order within each repetition. The default is 15 measured repetitions; it reports arithmetic means and dispersion. Incremental mode makes selected source edits; nonincremental runs remove the cache. The script intentionally tolerates diagnostic differences between revisions, so it is not a semantic-equivalence gate. [Comparison script](https://github.com/python/mypy/blob/0ff707d475eb967d1709409472dfe45644a8e6d3/misc/perf_compare.py)

The maintainer guide also distinguishes profiling compiled mypy from profiling a pure-Python version: the latter can misrepresent shipped performance. Its discussion of small repeatable shifts warns against treating more repetitions as a cure for every setup bias. [Profiling and optimization guide](https://github.com/python/mypy/wiki/Profiling-and-Optimizing-Mypy)

**Godot application:** profile the actual deployment build or label diagnostic builds separately. Include unchanged reruns, small source edits, and dependency-invalidating changes as different workflows. Preserve our independent behavior/coverage checks even when comparing revisions.

### ESLint: loading, one file, and many files

ESLint's inspected performance target creates a dedicated configuration and separately measures loading, a single large input, and a multi-file corpus. It invokes hyperfine with no shell, one warmup, and five measured runs. This is an explicit workload-size decomposition, not proof that every lint rule or plugin is represented. [Performance target](https://github.com/eslint/eslint/blob/fc81076a5b8145360654d81cbc130cf7d25dca77/Makefile.js)

**Godot application:** separate tool import/loading from single-script and project-wide execution. Record exact rules, parser, language version, and plugin configuration. Add worst-case syntax/rule interactions only when their behavior is defined and the result is correctly labeled.

### Semgrep: realistic rule/repository pairs and findings preservation

Semgrep's benchmark directory defines repository/rule configurations and variants that toggle optimizations. Its guide describes elapsed-time tracking and comparing findings with expected snapshots; some referenced historical dashboards are internal. Public source availability therefore does not imply all underlying historical measurements are public. [Benchmark guide](https://github.com/semgrep/semgrep/blob/ad20f09ece0b652f4e532803ce3bcf0e1586c618/perf/README.md)

The inspected findings comparator checks expected versus observed finding sets and reports missing/extra results. This illustrates a useful performance guard: a scan must still produce the required output. The comparator's assumptions and snapshot quality still require review. [Findings comparator](https://github.com/semgrep/semgrep/blob/ad20f09ece0b652f4e532803ce3bcf0e1586c618/perf/compare-bench-findings)

**Godot application:** make output agreement part of performance eligibility. For static-analysis studies, also record scanned and skipped files, rules, timeouts, parse failures, semantic mode, and dependencies. Never count a quicker scan of fewer files as equivalent improvement.

## Dedicated benchmark infrastructure

| System | Documented method | Suitable use here |
| --- | --- | --- |
| [pytest-benchmark](https://pytest-benchmark.readthedocs.io/en/latest/calibration.html) | Calibrates repeated function calls into timed rounds so timer resolution does not dominate. | Python helper microbenchmarks; rounds are not independent Godot launches. |
| [Google Benchmark](https://google.github.io/benchmark/user_guide.html) | Explicit CPU/real-time scopes, repetition, warmup, optional randomized interleaving, counters, and structured output. | Native parser/collector helpers; protect useful work from compiler elimination. |
| [BenchmarkDotNet](https://benchmarkdotnet.org/articles/guides/how-it-works.html) | Isolated Release builds, pilot sizing, workload/overhead warmup and measurement, and separate diagnostic work. | A model for lifecycle separation and explicit measurement overhead. |

BenchmarkDotNet documents subtracting the median of a matched empty-method overhead measurement from its workload measurements. That is a correction defined inside a particular microbenchmark model. It does not justify subtracting one average process-launch or profiler cost from every Godot scenario. Our harness/coverage/profiler interaction experiment remains necessary. [BenchmarkDotNet measurement model](https://benchmarkdotnet.org/articles/guides/how-it-works.html)

Framework defaults are conveniences with assumptions. Choose repetition, calibration, warmup, and stopping behavior for our actual estimand, and record overrides. Preserve the distinction between operations, iterations, process launches, sessions, and machines.

## Changes recommended for Godot Tooling

The following recommendations are our synthesis, not claims that all surveyed maintainers use the same protocol. They are integrated in the [methods addendum](../benchmarks/methods-addendum.md).

| Recommendation | Why it changes the study |
| --- | --- |
| Separate discovery, assertions, fixture setup, execution, and reporting. | A runner can regress before application logic begins; a single suite duration hides the cause. |
| Treat cold start, prepared launch, unchanged rerun, and edited rerun as separate states. | Cache and invalidation behavior are part of developer experience. |
| Keep synthetic diagnostic inputs and representative application scenarios. | One explains scaling; the other checks relevance. |
| Count equivalent work and validate outputs. | Faster incomplete instrumentation, fewer mutants, or missing findings must not win. |
| Record mutant throughput and total wait time separately. | Mutation generation and baseline/coverage work can dominate the complete command. |
| Maintain a small local/CI diagnostic suite and a controlled publication schedule. | Regression detection and externally defensible comparisons have different costs and requirements. |
| Keep raw observations, complete configuration, and publicly accessible artifacts. | A chart or inaccessible dashboard cannot support independent reproduction. |
| Profile the build and process that actually do the work. | A Python launcher profile, native engine profile, and GDScript profile answer different questions. |
| Calibrate overhead and investigate interactions. | A microbenchmark's empty-method correction cannot be assumed valid for an entire game workflow. |

For the first implementation slice, the highest-value additions are runner-phase boundaries, validated work counts, explicit cache/iteration state, and a clear path from a slow observation to an application or harness profile. Keep the existing independently reviewed coverage oracle and session-based analysis. The survey provides precedents, not a reason to weaken those controls.

## Limits and reproduction of this research

The ten repository snapshots are pinned in the inventory; official documentation and the mypy wiki are dated observations and may change. Source files were read, not executed. No performance ratios, compatibility claims, or upstream statistical guarantees were independently reproduced. A source-level omission is scoped to the inspected artifact and does not establish that the project has no other performance infrastructure.

The study should not copy upstream absolute timing thresholds, adopt reported speedups as Godot expectations, or pool unrelated tools' benchmark rows into a meta-analysis. The commonality is experimental structure; the languages, runtimes, semantics, hardware, and workloads differ.
