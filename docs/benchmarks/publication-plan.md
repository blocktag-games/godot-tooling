# Public study and publication plan

The intended audience is Godot developers, tooling maintainers, and people evaluating a possible open-source contribution. Publish a useful corpus and reproducible evidence before promoting a new framework. This revision publishes planning, not benchmark findings.

## Publication stages

| Stage | Public artifact | Claim boundary |
| --- | --- | --- |
| Protocol draft | This plan, catalogs, rationale, known gaps, and amendment history. | Proposed method and scope only. |
| Pilot package | Runnable vertical slice, provisional adapters, raw pilot observations, protocol changes. | Feasibility and methodological findings; no broad performance ranking. |
| Frozen study protocol | Tagged sources/oracles, tool pins, schedule, metrics, analysis plan, exclusions. | Public precommitment before main-study interpretation. |
| Study release | Complete raw data, validator output, scripts, report, figures, reproducible cases. | Observed results on the named configurations and machines. |
| Independent reruns | Contributor environment records, artifacts, and differences from the protocol. | Reproduction/replication scope stated explicitly. |
| Follow-up synthesis | Versioned evidence table; quantitative synthesis only if justified. | Claims supported by compatible independent evidence. |

Use versioned releases and immutable artifact hashes. Link the protocol revision actually used for each result. A changing default branch is a discovery link, not a substitute for the frozen study. A persistent archival identifier can be added when a host is chosen; do not claim archival permanence or an external review badge merely by uploading a GitHub release.

## Report outline

1. State the questions, reference configurations, main observations, and limits in plain language.
2. Describe candidate selection, version cutoffs, license/component boundaries, and installation outcomes, including unavailable candidates.
3. Define coverage obligations and denominators with a small example readers can inspect.
4. Present compatibility, correctness, completeness, and behavioral preservation before performance.
5. Show elapsed/resource effects with absolute quantities, paired ratios, uncertainty, sample hierarchy, and failures.
6. Explain selected bottlenecks using profiles and include the observer-effect study.
7. Demonstrate debugger/IDE workflows, distinguishing documented possibilities from executed evidence.
8. Discuss threats to validity, unresolved discrepancies, and where each configuration may be useful.
9. Link reproduction commands, artifacts, analysis, known issues, and the resulting project architecture decision.

Avoid “Godot has no testing/debugging/static analysis,” “all coverage tools are inaccurate,” or “fastest” without a defined comparison population. The [survey](../research/2026-09-06-godot-tooling-survey.md) already establishes substantial prior art. Passing a finite corpus, a narrow engine version, or one machine does not establish universal compatibility.

## Tables and figures

| Figure/table | Source data | Presentation requirement |
| --- | --- | --- |
| Capability matrix | Every scheduled tool/mode/fixture outcome. | Distinguish matched, mismatch, unsupported, unavailable, incomplete, and untested; include counts. |
| Coverage discrepancy example | Source, oracle, native report, mapping. | Show original lines and the smallest understandable counterexample. |
| Per-workload overhead plot | Paired runs and declared estimates. | Ratio reference at 1, intervals, absolute times, named baseline, condition scope, and failure counts. |
| Timing distribution and drift | Raw durations, session/order metadata. | Show variation and order effects; avoid only a single mean bar. |
| Scaling curves | Fixed input sizes and work counts. | Label scripts, lines, branches, calls, or bytes rather than vague project size. |
| Observer interaction plot | H/C/P blocks. | Separate main effects and interactions; name profiler and build. |
| Phase/profile view | Captures and phase attribution. | Mark inclusive/overlapping spans; do not sum overlapping costs. |
| Reproduction table | Independent environment and run records. | Show exact protocol deviations and failed reproduction attempts. |

Generate publication figures with standard plotting tools and export standalone SVG/PNG plus source CSV/TSV. Include units, readable labels, captions, alt text, and color-independent state markers. An optional interactive explorer may filter the same dataset, but every main claim must remain inspectable in the static report. Do not generate illustrative performance charts that could be mistaken for observations.

## Fair comparison and review

Apply the same documented inclusion criteria and setup effort budget to candidates. Record unavailable modes and install failures as scoped observations, not proof that a project never works. Verify suspected defects against documented usage and isolate minimal reproductions. Keep native results separate from locally fixed versions.

Provide a factual review package for maintainers: pinned version, commands, expected/actual behavior, relevant logs, and draft wording. Maintainer feedback can correct setup errors, clarify contracts, or suggest a separate follow-up configuration. Preserve the original study record and amendment trail. Maintainers do not need to endorse conclusions for the report to exist.

Sending messages, opening external issues, or submitting contributions is a separate action requiring the project owner's authorization. Preparing review material is part of the study. A suggested review window is one to two weeks, adjusted to actual participation; no outreach has been scheduled or sent by this planning revision.

Disclose project motivation, evaluated-tool contributions/forks, funding or free licenses if any, and who authored fixtures and analysis. Keep a record of reviewer contributions. Do not let a hoped-for new product dictate which results appear.

## Release readiness

Before calling a study release complete:

- Every planned cell has attempts or an explicit reason it could not run, including missing platforms and failed installations.
- Oracles, adapter mappings, behavior checks, and completeness checks have evidence; unresolved truth disputes are labeled.
- The analysis includes the frozen primary comparisons, failed-run accounting, deviations, sample hierarchy, and uncertainty limitations.
- All report values and figures regenerate from supplied data with a pinned analysis environment.
- At least one person or separately recorded clean environment follows the reproduction instructions; state which kind of validation actually occurred.
- Artifacts have a manifest and hashes; source and data provenance, license notices, and necessary publication transformations are recorded.
- The report distinguishes a demonstrated result, an inference, and a proposed improvement.

Publish this repository's original code/documentation under its existing Apache-2.0 license. Evaluated tools, external assets, profiler captures, and binaries retain their own terms; verify permission before including third-party material in a bundle. Prefer acquisition recipes and hashes for components that cannot be redistributed. The partly closed comparator must not become a prerequisite for using or reproducing the open benchmark core.

Use an allowlist of scientific artifacts for publication. Profiles and logs can include machine paths or unrelated process details; capture the narrow required scope, retain a documented public path mapping, and review the exported bundle. A transformed public artifact must have its own hash and provenance. Do not alter measurement values while sanitizing metadata.

## Limitations, corrections, and decisions

Discuss at least: candidate selection, incompatible versions, ambiguous line semantics, oracle errors, runner differences, patched builds, missing features, workload representativeness, timing/observer bias, shared-machine noise, correlated observations, failure-conditioned performance, and limited hardware/platform coverage. Experimental control and typical developer realism are different study settings.

Keep releases immutable. Corrections get an erratum with affected claims/artifacts, cause, corrected analysis, and a new release link. A provider fix gets a new pinned evaluation. Do not silently replace old data or delete inconvenient failed runs.

The final architecture decision should weigh evidence in separate dimensions: measurement trust, scope, maintenance across Godot versions, installation, runtime cost, complete implementation openness, and IDE workflow. A useful result might be upstream fixes plus adapters and this shared corpus. A new collector becomes justified only by documented requirements that existing options cannot reasonably meet.
