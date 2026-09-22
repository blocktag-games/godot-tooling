# Architecture decision: extend, integrate, or build new

Per `publication-plan.md`'s requirement: weigh evidence across measurement trust, scope, maintenance across Godot versions, installation, runtime cost, complete implementation openness, and IDE workflow. This is a decision record, not a new claim — every factual input below is cited to the section of `final-report.md` (or the underlying fixture/study) that demonstrated it.

## Options considered

1. **Do nothing / recommend as-is.** Neither tool needs replacing to be useful; document known gaps for users.
2. **Upstream fixes plus this shared corpus as an ongoing regression suite.** Report the findings in `maintainer-review-package.md` upstream (pending owner authorization to send), and offer this project's fixture corpus as a reusable, versioned test suite either maintainer could adopt.
3. **A thin compatibility/normalization adapter layer** in front of one or both tools, translating native reports into a documented, corrected obligation model (e.g., fixing the `if_true`-fires-on-evaluation semantics at the adapter layer without needing an upstream code change).
4. **A new collector**, built from scratch for Godot 4.7.1+.

## Evidence by dimension

| Dimension | gd-tools-cli 0.4.0 | Nano Coverage | Implication |
| --- | --- | --- | --- |
| **Measurement trust** | 4 real root-cause defects across 13/53 corpus inputs (`final-report.md` §4); F057/F082 line-shift confirmed | 3 real root-cause defects across 6/53 corpus inputs; F082 line-shift newly confirmed here | Both tools are usable but neither is fully trustworthy for line-exact claims without the specific caveats this study documents. Neither defect set is disqualifying on its own. |
| **Scope** | Line + branch coverage, GUT-bound | Line coverage (LCOV), GdUnit4-hook-bound; no branch counters at all (corpus sweep: "zero BRDA records") | gd-tools has strictly broader scope (branch tracking exists, even if imperfect); this is a real capability gap for Nano Coverage, not a defect. |
| **Maintenance across Godot versions** | Actively released (`v0.4.0` current at pin time); depends on GDScript source-injection, which is inherently version-fragile if GDScript's own reload/compile internals change | Native GDExtension pinned against godot-cpp's 4.3-era API bindings while targeting 4.7 — confirmed working, but a real version-skew risk already visible in the pin record itself (`nano-coverage-godot-PIN.md`) | Nano Coverage's cross-version risk is more concretely evidenced (an already-observed API-generation mismatch) than gd-tools', which is more of a structural argument. |
| **Installation** | Pipenv install, no issues, within one-day budget | Requires building from source (`scons`, no sudo needed but real local build effort); one packaging bug had to be worked around directly (`.gdextension` naming mismatch) | gd-tools installs more easily for an end user; Nano Coverage's build step is a real adoption friction point, already demonstrated, not hypothetical. |
| **Runtime cost** | 1.06x–12.4x work-time overhead depending on workload (`final-report.md` §5); B1 (installed, inactive) is free | 3.0x–9.7x work-time overhead on the same workloads | Neither tool is cheap on branch-heavy code; both are cheap-to-free on simple code. Absolute added seconds, not percentage, is the fair comparison (§5) — on the shared branch-heavy workload gd-tools' absolute added cost is actually larger despite the smaller percentage. |
| **Complete implementation openness** | Apache-2.0-compatible per `pilot-environment.md`'s pin record | Apache-2.0, confirmed directly against `LICENSE.md` | No licensing obstacle to either upstream contribution or a corpus-based regression suite for either project. |
| **IDE workflow** | Debugger launch/attach confirmed working; automatic error-break reports the wrong (shifted) line (§8); explicit breakpoint binding unverified for either candidate (a harness limitation, not a demonstrated tool defect — see §8's own scoping) | Same debugger-protocol shift confirmed (§8, F082); same breakpoint-binding gap | Both tools share the exact same debugger-visible defect (shifted lines), because both instrument the live source in a way the engine's own diagnostics can't distinguish from original code. This is the single most actionable, tool-independent finding of the whole study. |

## Decision

**Recommend option 2 (upstream fixes plus this shared corpus), with option 3 (a thin normalization adapter) as a fallback for defects that don't get fixed upstream in a reasonable window.** Reasoning:

- No requirement demonstrated by this study needs a new collector (option 4) to meet. Both existing tools already cover the core use case (line coverage in CI, coverage-driven test authoring); their defects are specific, bounded, and independently fixable — not systemic failures of the whole approach.
- The line-shift defect (F057/F082) is the sharpest, most actionable finding, and it is **architectural, not incidental**: both tools instrument by modifying in-memory source before the engine's own compile/reload step, and the engine has no source-map mechanism to compensate. A hypothetical future collector that instrumented at the VM/bytecode level *without* rewriting the source text presented to the compiler would not have this defect by construction — this is worth stating explicitly as a design constraint for any future contribution, upstream fix, or (if ever pursued) new collector, even though building one from scratch is not justified by anything else in this study.
- Doing nothing (option 1) leaves real, now-documented defects unreported to the people who can fix them, which conflicts with this project's own stated goal ("help maintainers reproduce defects" — `docs/benchmarks/README.md`).
- A full adapter layer (option 3) as the PRIMARY strategy would mean maintaining a permanent translation shim against two upstream projects' internal behavior indefinitely — reasonable as a stopgap for any specific defect upstream declines or delays fixing, but not preferable to a real fix when one is achievable.

**Not yet decided, and explicitly not this document's call:** whether to actually send the maintainer review package. That requires the project owner's separate authorization per `publication-plan.md`'s own rule, which this document does not grant itself.

## What would change this decision

- If either upstream maintainer declines the line-shift finding as "won't fix" (e.g., treats the in-memory injection approach as fixed and not worth a source-map layer), the adapter-layer fallback (option 3) becomes the practical recommendation for that tool specifically.
- If a future Godot engine release changes GDScript's reload/compile internals in a way that breaks source-injection instrumentation outright (a real, evidenced risk per the maintenance-dimension row above), this decision should be revisited against whatever collectors still function.
- BP12 (cross-platform/multi-machine replication) remains descoped by explicit decision, not oversight (`implementation-plan.md`'s BP12 row); this decision record does not depend on multi-machine evidence and should not be read as implying such evidence exists.
