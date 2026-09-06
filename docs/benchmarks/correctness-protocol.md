# Coverage correctness protocol

Draft specification; all fixtures and adapters remain to be implemented. See the [study plan](README.md) and [fixture catalog](fixture-catalog.tsv).

## Establish truth independently

Each fixture contains a small application, specified inputs, observable expected behavior, and a hand-reviewed execution oracle. The oracle describes original source locations and control-flow outcomes without using the evaluated collector's parser, instrumentation plan, or reports to generate expected results.

For each fixture, first compile and run the uninstrumented application on the pinned engine. Compare its output with the behavioral specification. An engine rejection or baseline behavior mismatch blocks that fixture on that engine. Retain it as engine incompatibility or a fixture defect; do not count it as a collector failure. Disagreements between two collectors are evidence to investigate, not a majority-vote oracle.

Review expected hits by tracing the small program's inputs and execution paths. Use deliberate input changes and independent behavioral observations to challenge the oracle. A second human review is desirable before public correctness claims; record author/reviewer identities and unresolved ambiguities. Any added diagnostic probes belong in a separate validation variant, since they can themselves alter execution.

For large workloads, expected output, selected known execution facts, and metamorphic checks are practical. Label this evidence as partial. A checksum alone does not prove every coverage entry is correct.

## Define the measurement contract

Record the following contract per candidate configuration before interpreting percentages:

| Dimension | Required definition |
| --- | --- |
| Source population | Exact application file manifest and hashes, include/exclude rules, generated files, add-ons, and never-loaded files. |
| Collection interval | Earliest tracked lifecycle event and last flushed event; initialization, test hooks, gameplay, and shutdown boundaries. |
| Line eligibility | Original executable source locations; treatment of declarations, continuations, annotations, comments, and multiple statements on one line. |
| Line hit | Whether a location was reached; distinguish statement entry, successful completion, and any constituent expression executing. |
| Count | What a numeric counter counts: entries, calls, iterations, resumptions, or another event. If unestablished, retain raw counts without asserting count accuracy. |
| Function | Stable identity for named functions, lambdas, inherited methods, and implicit lifecycle code; entry and exit are separate events. |
| Branch | Stable decision and outcome identities; explicit and implicit alternatives, loops, match outcomes, and short-circuit evaluation. |
| Concurrency | Process/thread identity, supported synchronization, collection loss detection, and merge rules. |
| Completeness | Evidence of successful instrumentation, execution, flushing, parsing, and source accounting. |

Use two views: agreement with the tool's documented contract and satisfaction of our desired developer requirements. For example, a collector that explicitly starts after autoload initialization may agree with its contract while leaving startup coverage unsupported. A selected file silently lost after an instrumentation failure is a completeness problem, not simply an uncovered line.

Line, statement, function, decision/branch, condition, and MC/DC coverage are distinct. For the common branch comparison, define obligations as named outcomes of source-level decisions. Evaluate condition and short-circuit obligations in separate extensions when supported. Do not interpret an LCOV branch identifier as a shared cross-tool semantic identity without a verified mapping. Do not infer condition coverage from an advertised branch percentage.

## A minimal oracle example

This illustrative source is an oracle design example, not an implemented or engine-validated fixture:

```gdscript
extends RefCounted

func classify(value: int) -> int:
	if value > 0:
		return 1
	return 0
```

With one call `classify(2)`, original lines 4 and 5 are reached and line 6 is not. The decision on line 4 takes its true outcome and leaves its false outcome untaken; the function is entered once. Under our body-line convention, lines 1–3 are not executable body-line obligations. A provider that also counts a declaration receives an explicit semantic mapping, not an unexplained percentage mismatch.

With a second call `classify(0)`, lines 4 and 6 are reached in that call and the other decision outcome is taken. The union covers both outcomes. After implementing the fixture, bind this oracle to the exact file hash; line edits invalidate that binding until reviewed. Add a never-called function and a never-loaded second file as independent fixtures rather than expanding this example until its truth is difficult to inspect.

Store each obligation's stable ID, original file/hash/span, kind, eligibility explanation, expected hit state by named input, and expected count only where unambiguous. Keep line numbering one-based. For multi-statement lines, retain statement obligations internally and derive the agreed line view explicitly.

## Execute and compare

1. Create an isolated workspace from the pinned fixture manifest. Record clean source hashes and expected source inventory.
2. Run the uninstrumented application and validate return values, state transitions, ordered events where specified, output files, and exit behavior.
3. Run the same application inputs through a supported collector workflow. Keep GUT, GdUnit4, and manual drivers thin; validate that their application invocation traces agree.
4. Capture the original report, logs, collection interval, instrumentation diagnostics, process outcomes, and pre/post source hashes before cleanup.
5. Normalize without inventing absent data. Compare original source obligations and record mismatches with references to raw evidence.
6. Check recovery: launch a fresh baseline in a fresh process, inspect artifacts, and verify that source and user data isolation held.

Separate single-input runs, cumulative runs, and explicit report merges. They test different behavior. Run each deterministic core case at least three times in fresh processes for the initial correctness pass; this is a reproducibility check, not a statistical reliability claim. Concurrency and cancellation stress cases use a pilot-selected fixed schedule and repetition budget, recorded before interpretation.

## Coverage accounting

Publish raw counts alongside any fraction: expected eligible obligations, provider-eligible obligations, expected hits, matched hits, false hits, missed hits, missing selected files, unsupported obligations, and unmappable records. A missing record becomes a zero hit only when the provider's verified sparse-report semantics establish that interpretation and the selected source inventory is complete. Otherwise it is unknown.

On a fully comparable set, `matched expected hits / expected hits` describes hit recall, and `matched expected hits / reported hits` describes hit precision. These supplement exact differences; they do not replace source-population checks. A zero denominator is `not_applicable`, never automatically 100%. Report provider-native percentages alongside normalized percentages only with their respective denominators and scope.

If line support is correct but branch measurement is unsupported, show both facts. Do not assign zero branch accuracy, and do not exclude the project from the public capability matrix. A performance comparison may use a common line-only mode if one really exists; broader modes get separately labeled results. Unmapped obligations prevent a claim of full semantic equivalence.

## Corpus design

The machine-readable catalog divides cases into source population, line semantics, control flow, language features, lifecycle, concurrency, failures, merging, integration, and portability. Tier 0 is a small vertical slice; tier 1 establishes the primary contract; tier 2 extends stress and integration. Every row is planned and must acquire source, inputs, oracle, and engine validation before execution.

Include positive controls (known covered paths), negative controls (known unexecuted code), boundary cases, and deliberately invalid configurations. Failure fixtures isolate one fault at a time and state whether that fault belongs to the application, collector, harness, or external termination. GDScript error cases use actual engine error behavior; do not assume exception semantics from another language.

Metamorphic relations provide additional checks:

- Adding a never-called function changes the declared denominator without changing earlier hits.
- Repeating a deterministic invocation preserves the hit set; exact counter multiplication is expected only under a validated count contract.
- Combining complementary inputs yields the expected union; reversing independent inputs preserves that union.
- Renaming a file or moving the workspace preserves behavior and maps coverage to the new original source identity.
- Changing only comments or line endings preserves logical obligations after an explicit source-map update, not a stale line-number comparison.
- Merging the same run twice must be rejected or have documented deduplication/aggregation semantics. Distinguish hit-set idempotence from counter summation.

## Behavior, robustness, and integration

Compare deterministic results exactly. Where floating point, scheduling, or rendering makes exact equality inappropriate, define an invariant or tolerance from the uninstrumented specification before covered runs. Keep timing-dependent behavior in a separately labeled sensitivity experiment; coverage can slow execution enough to change real-time outcomes without corrupting a computation.

Exercise failed instrumentation, parse errors, runtime errors, zero tests, aborts, crashes, timeouts, output truncation, source edits, stale reports, concurrent sessions, and cleanup failures. The public report must distinguish application failure from collector failure and preserve partial evidence. Terminating a process forcibly cannot be expected to execute its cleanup handlers; evaluate detection and next-start recovery as well as graceful cleanup.

For live debugging, test original source breakpoints, verified binding, stepping, stack frames, variables, await resumption, and a failed-test launch. Record the exact IDE edition/build and plugins. Coverage gutters and debugger location mapping are separate checks. Pause-time and debugger attachment invalidate ordinary performance measurements, so these cases belong in the integration lane.

A candidate's correctness section is ready to publish when every scheduled cell has a supported/unsupported/unavailable outcome, discrepancies have minimal reproductions where possible, and the report names the exact scope in which agreement was observed. There is no assertion that passing this finite corpus proves a collector universally correct.
