# Benchmark implementation roadmap

Status on 6 September 2026: protocol and catalogs drafted; implementation and execution have not started. Work packages below are ordered by dependency. Estimates are planning ranges for one active contributor and will be revised after the first runnable slice.

## Work packages and completion evidence

| ID | Package | Depends on | Completion evidence | Initial effort |
| --- | --- | --- | --- | --- |
| BP01 | Freeze pilot scope and environment identity. | This draft | Actual engine/hash/build, chosen machine, candidate pins, runner pairings, pilot schedule, explicit unavailable modes. | 1–2 days |
| BP02 | Implement the first independent fixtures and oracles. | BP01 | Tier-0 cases compile/run uninstrumented; documented inputs, expected behavior, hashes, reviewed obligations. | 2–4 days |
| BP03 | Implement minimal orchestration and evidence records. | BP01 | Isolated workspaces, structured outcomes, logs, timeouts, source checks, artifact validation; synthetic failure controls pass. | 2–4 days |
| BP04 | Add the first coverage adapter. | BP02, BP03 | Baseline and covered runs of the same case; native/normalized reports; exact mismatches; one-command reproduction. | 2–4 days |
| BP05 | Add remaining candidate modes and parity drivers. | BP04 | Thin GUT/GdUnit4/manual drivers, available configurations installed, unresolved setup limits recorded. | 3–7 days |
| BP06 | Complete primary correctness corpus. | BP05 | Tier-1 outcomes, source-population checks, failure evidence, minimal reproductions, oracle review record. | 4–8 days |
| BP07 | Implement deterministic performance workloads and pilot. | BP04; selected BP06 cases | Fixed input/behavior checks, phase boundaries, matched baselines, pilot variance and cost report. | 3–6 days |
| BP08 | Validate profiling and measure the harness. | BP03, BP07 | Null/CPU/wait/log/memory controls, independent timing cross-check, one useful script/native/harness capture where available, pilot observer matrix. | 3–6 days |
| BP09 | Freeze main study and analysis. | BP06–BP08 | Tagged protocol and oracles, eligible cells, exact repetition/analysis rules, validated analysis on synthetic known data. | 1–3 days |
| BP10 | Run controlled Linux study. | BP09 | Complete schedule/attempt accounting, raw artifacts, environment checks, independent sessions, generated result tables. | 3–5 calendar days plus machine time |
| BP11 | Verify debugger and PyCharm workflow. | BP05, BP06 | Exact IDE build/plugins, launch/attach, verified original-source breakpoints, stepping/state, failed-test path, coverage navigation. | 2–5 days |
| BP12 | Add OS and machine replication. | BP06, BP09; hardware access | Clean Windows/macOS correctness as available; separately labeled performance replication and deviations. | 2–5 days per environment |
| BP13 | Write, review, and publish the study. | BP10, BP11; available BP12 evidence | Rebuildable report, complete artifacts, limitations, maintainer review material, independent reproduction record, architecture decision. | 3–6 days plus optional review window |

These ranges are not a promised delivery date and do not include unlimited upstream debugging, new engine builds, or waiting for hardware/reviewers. Some work can overlap operationally, but no multi-person staffing is assumed. The first usable contribution is BP04, not completion of every catalog case.

## First executable slice

Start with gd-tools/GUT because the survey identified an integrated CLI workflow; if the actual pinned setup fails, retain that evidence and move to the next feasible candidate. This is an evaluation order, not a product preference. No adapter should require rewriting the application fixture to suit the collector.

Implement the tier-0 catalog: never-loaded file, uncalled function, simple line execution, both and implicit branch outcomes, startup/autoload boundary, awaited continuation, deterministic behavior, failed instrumentation, zero requested tests, abort, and source-aware merge. Some fixtures need multiple named input runs; count those runs explicitly.

Build one baseline-to-report path with source hashes, a native report, normalized obligation differences, and a readable result record. Prove a false hit, missing file, stale report, or truncated report cannot silently become a successful complete measurement in our own harness using synthetic adapter inputs. These tests protect the evidence pipeline.

The first public pilot should let a reader run a small correctness case and rebuild its comparison. It should also show an empty-run timing control and one substantive workload. Do not wait for a dashboard, cross-platform installer, or a new coverage engine.

## Stage the matrix rather than multiply every factor

The [experiment matrix](experiment-matrix.tsv) identifies experiment families. Expand selected families into exact tool/mode/workload/engine/platform cells in BP01 for the pilot and BP09 for the main study. Every expanded cell needs an ID, eligibility rule, schedule, and disposition. The matrix is not an instruction to run the full Cartesian product.

Initial main-performance scope is W01, W03, W05, and W11 on Linux with three open candidate configurations where feasible. Use one supported runner/mode per candidate for that primary set; additional modes and scaling are separate extensions. Keep the partly closed comparator's within-limit feature checks and boundary cases separate from unrestricted scaling. Exceeding a published file limit must not be used as evidence of ordinary scalability failure.

For a planning example with three candidates, four workloads, ten sessions, six blocks per session, and three B0/B1/C conditions, the primary set is `3 × 4 × 10 × 6 × 3 = 2,160` process invocations. With only B0/C it is 1,440. This excludes pilots, fresh imports, profiling, repeats after invalid attempts, and other runners/platforms.

At an illustrative 5 seconds per process, 2,160 invocations alone take 3 hours; at 15 seconds, 9 hours. Preparation, imports, capture, validation, thermal/session spacing, and analysis add time. These are arithmetic budget scenarios, not measured runtimes. BP07 must produce the real budget before BP09 freezes the schedule.

An eight-condition observer experiment costs `workload/collector/profiler combinations × sessions × blocks × 8` invocations. A three-workload, one-collector, one-profiler pilot with two sessions and five blocks costs 240 launches; the ten-session/six-block version costs 1,440. Select the main-study combinations based on explicit methodological questions, not whichever pilot result looks most dramatic.

Large traces may dominate storage. Record bytes per capture in BP08, estimate the planned total plus retention headroom, and choose a versioned archive before the main study. Keep source/analysis in Git and bulk artifacts outside ordinary Git history.

## Proposed implementation layout

When BP02–BP04 begin, create fixtures grouped by case ID, reviewed oracle files, thin runner drivers, a harness package, provider adapters, schema validators, workloads, analysis scripts, and reproduction documentation. Keep the current planning documents in `docs/benchmarks/`. Avoid empty scaffold directories until they have useful content.

Use routine CI for schema/link integrity, harness failure controls, a small baseline/correctness subset, and report regeneration from small checked-in examples. Pin engine/tool dependencies. Hosted CI performance remains a smoke signal, not a public speed ranking. Native extension builds and IDE automation can join the matrix when reproducible and maintained.

## Decisions and risks

| Item | Current planning position | Resolve by |
| --- | --- | --- |
| Hardware and OS access | Linux first; controlled machine availability and Windows/macOS access unconfirmed. | BP01 and BP12 |
| Engine target | Godot 4.7.1 reference; exact binary/build still to pin. | BP01 |
| Candidate installation budget | Initially one working day per configuration before recording unresolved setup and moving on; publish actual effort and follow-ups. | BP01 |
| Oracle ambiguity | Record alternative contracts and defer universal claims; never derive truth from a favored collector. | BP02/BP06 |
| Missing B1 or phase controls | Mark unavailable; measure complete workflow with explicit confounds. | BP04/BP07 |
| Patched/closed comparator | Optional feature comparison; obtain exact permitted binaries and within-limit scope. | BP05 |
| Profiler access/build effort | Linux perf first if available; Godot/script and Python captures where feasible; Tracy is a separate build experiment. | BP08 |
| Workload sizes and sample counts | Proposed defaults only; choose using pilot variance and cost, then freeze. | BP09 |
| Public dataset hosting | GitHub release assets or a versioned archive, with hashes; provider undecided. | BP09/BP13 |
| PyCharm support | Exact edition/build/plugins must be demonstrated; no assumption based on Rider. | BP11 |
| Independent review | Oracle review and reproduction participation to recruit when artifacts exist. | BP06/BP13 |
| New tool architecture | Remains open pending evidence; upstream contribution is a valid outcome. | BP13 |

Document protocol amendments with date, affected question/cells, reason, whether data had been seen, and effect on interpretation. Preserve failed approaches as evidence only when they explain a result or limitation; keep the public instructions centered on the final reproducible workflow.
