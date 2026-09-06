# Reproducibility and artifact contract

This document specifies the proposed harness and data model. Directories, interfaces, schemas, and commands described as future work do not exist yet. The [implementation plan](implementation-plan.md) schedules them.

## Architecture and adapter boundary

Prefer a small Python orchestrator with GDScript fixtures, ordinary subprocesses, versioned JSON/TSV artifacts, and thin provider adapters. Python is a provisional implementation choice because several candidate workflows already use it and it suits cross-platform orchestration. Pin its version and dependencies at implementation time. Native code belongs in evaluated providers or a justified measurement helper; a new collector or engine fork is not required to build the benchmark.

The future logical adapter interface should provide:

| Operation | Responsibility | Evidence to retain |
| --- | --- | --- |
| Probe | Identify binary/package, dependencies, modes, and observable capabilities. | Exact versions/hashes, discovery output, unsupported reasons. |
| Prepare | Materialize a disposable project with explicit runner/collector configuration. | Source manifest, generated configuration, transformation records. |
| Baseline | Resolve valid B0/B1 variants or explain why a variant is unavailable. | Exact argument vectors and differences from coverage condition. |
| Execute | Launch, bound execution, capture outputs, and expose available phase events. | Commands, processes, clocks, exit/test/completion outcomes, logs. |
| Collect | Preserve native reports and completeness signals. | Original bytes, source inventory, instrumentation/flush diagnostics. |
| Normalize | Map only established semantics into the shared result model. | Adapter revision, mapping rules, unmapped entries, raw provenance. |
| Recover | Inspect source changes and cleanup/recovery behavior. | Pre/post hashes, backups, leftovers, next-launch behavior. |

Installation should be a separate explicit setup step with pinned artifacts. It must not download a changing dependency during a timed run. Separate native release behavior from local patches; label both configurations. Never silently patch a provider to make its benchmark pass.

Validate adapters with deliberately malformed reports and known expected normalization results. Test the harness where it could invalidate evidence: dropped output, wrong exit propagation, stale artifacts, source mismatch, process-tree timeout, clock boundaries, and wrong condition pairing. Do not spend the first milestone building a generic plugin platform.

## Isolation and lifecycle

Every attempt gets a unique run ID and fresh writable project/output directories. Original fixtures remain immutable. Record selected source before instrumentation and inspect disposable workspace changes before removing it. Disk-instrumenting tools operate on these copies. A forced termination may leave a disposable workspace dirty; retain evidence and validate the tool's documented recovery path.

Assign a distinct Godot user-data location, test output root, and relevant cache/config roots through supported engine/OS configuration. Validate actual isolation with sentinel files rather than assuming a flag worked. Never use a developer's real save profile. Record project import state and runner/plugin installation state separately. Use equivalent prepared snapshots per condition for warm runs; fresh-import runs start without generated import state.

The harness owns the process group/job it launches. Timeouts terminate that group using platform-appropriate graceful and forced stages, then reap children and capture final evidence. Record requested timeout, grace interval, signals/actions, residual processes, and actual termination. An IDE-launched game may escape a simple parent-child tree; validate that path before automated integration runs.

Use unique report locations and reject a report with a stale run/source identity. If the native format has no run identity, establish provenance through the isolated output directory, invocation record, timestamps where useful, and artifact hashes; do not invent native guarantees. Detect incomplete writes before parsing. Keep output caps explicit and mark truncation.

## Study and run identity

Freeze a study manifest before the main run. It links the protocol commit, fixture/oracle revisions, tool lock records, environment records, planned cell list, randomized schedule, analysis revision, exclusion/retry policy, and amendment history. Each scheduled cell must resolve to attempts or an explicit unavailability record.

Each run manifest needs these field groups:

| Group | Required fields |
| --- | --- |
| Identity | Schema version; study/cell/session/block/run IDs; attempt number; pilot/main/diagnostic classification; UTC start; links to related baseline and profile runs. |
| Sources | Repository revision and dirty state; fixture/input/oracle hashes; per-file source hashes; selected/instrumented/reported populations. |
| Software | Engine version, executable hash, build type/options where known; provider/runner versions and revisions; adapter/harness/analysis versions; package lock and dependency identities. |
| Command | Executable, argument array, working directory, configuration files, allowlisted environment overrides, resolved paths, installation recipe. |
| Conditions | B0/B1/C; harness/profiler mode; coverage kinds; include/exclude rules; import/cache state; renderer; fixed work/input seed; warmup; timeouts. |
| Machine | Stable public machine ID and detailed environment record; session checks and deviations. |
| Measurements | Value, unit, metric name, process/thread scope, phase boundary, clock domain, sample count/rate, measurement mechanism, availability reason. |
| Outcomes | Execution, behavior, collection completeness, semantic agreement, restoration, performance eligibility, and reason codes. |
| Artifacts | Relative path, kind, byte count, hash, originating command/run, and any publication transformation. |

Use explicit units in field names or typed measurement records. Store elapsed time as integer duration units with a stated clock, byte counts as integers, and missing values as `null` plus a reason. Zero is an observation, not missing data. Preserve UTC wall-clock metadata for chronology and monotonic elapsed values for duration.

Record safe, relevant environment values rather than dumping the entire environment, which can contain credentials. Use a documented path mapping for public artifacts so local usernames/home paths do not become identifiers. Preserve logical paths and source hashes for reproducibility. Any redaction must be recorded without altering scientific measurements.

## Outcome states are independent

One Boolean success flag cannot describe a coverage run. Use orthogonal fields:

| Field | Proposed values |
| --- | --- |
| Execution | completed, failed, timed_out, crashed, setup_failed, unavailable |
| Application behavior | matched, mismatched, not_checked, not_applicable |
| Collection completeness | complete, partial, unknown, not_applicable |
| Semantic agreement | matched, mismatched, unsupported, unmappable, not_checked, not_applicable |
| Source restoration | restored, changed, recovery_required, unknown, not_applicable |
| Performance eligibility | eligible, ineligible, exploratory, with explicit reasons |

A failed application may still produce a correct partial report. A successful process may have measured zero requested tests. A report can be syntactically valid but semantically wrong. Keep native exit status, runner test counts, instrumentation failures, and flush status alongside the normalized fields.

For data-model examples, use a dedicated examples directory with `example: true` and no measured values. Do not mix illustrative rows with real study data. Catalog rows in this planning revision use `planned`, which is a planning state and must not be accepted as a completed run outcome.

## Normalized coverage model

Retain provider-native reports unchanged. The normalized view links each record to its raw source and mapping rule. File identity combines logical project path and original content hash. Function/decision/statement IDs are defined by the reviewed oracle and verified adapter mappings, not by assuming every provider's generated IDs agree.

For every obligation, store kind, original source span, expected state, observed state, optional count/semantics, eligibility, and provenance. Observed states include hit, not_hit, unknown, unsupported, and unmappable. File records include whether selected, successfully instrumented, loaded where observable, and reported. Capture the collection interval and language/build limitations at run level.

Schema validation checks types and invariants; it does not prove measurement truth. Additional validators check source identity, report totals against records, branch outcome mappings, run pairing, duplicate merge inputs, clock boundaries, and full scheduled-cell accounting. Preserve any provider totals that disagree with its detailed records.

## Proposed release layout

The implementation should produce a study bundle with the following logical structure:

```text
study.json                    frozen protocol and artifact index
locks/                        exact tools, engines, dependencies, builds
environments/                 public machine and session records
schedule/                     planned cells, seeds, attempt accounting
runs/<run-id>/manifest.json   identity, configuration, outcomes
runs/<run-id>/raw/            native reports, stdout, stderr, events
runs/<run-id>/normalized/     coverage and measurement records
profiles/<capture-id>/        raw captures, metadata, useful exports
analysis/                     pinned scripts and derived tables
report/                       report, static figures, figure source data
checksums.sha256              bundle integrity checks
```

Put small fixtures, oracles, schemas, adapters, and analysis code in Git. Store large immutable logs/traces/data archives as release assets or a suitable versioned archive, linked and hashed from the report. No storage provider is selected yet. Containers can document dependencies, but performance claims must describe the container/host relationship; an image hash alone does not specify hardware.

The eventual reproduction entry points should cover environment probing, one correctness case, one pilot performance cell, full scheduled execution, artifact validation, and report rebuilding. Publish actual tested commands when implemented. Documentation must not present a speculative CLI as currently usable.

Require a fresh checkout to rebuild all published tables and figures from the bundle without rerunning the expensive measurements. Separately validate that a reader can execute one small fixture from the documented setup. These are distinct reproduction tasks.
