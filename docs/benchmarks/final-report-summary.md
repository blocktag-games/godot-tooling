# GDScript coverage tooling: final study

*2026-09-21. Reader-facing version of [final-report.md](final-report.md), which carries the full citations and file paths behind every claim here.*

Coverage tools for Godot's scripting language work, but with three real caveats: they miss some code, they slow tight loops by roughly ten times, and they point error messages at the wrong line. This report tests two tools against Godot 4.7.1 on one Linux machine and recommends fixing them upstream rather than building a replacement.

## What was tested and why

Code coverage tells you which lines of your program your tests actually ran. For Godot's scripting language, GDScript, a handful of community tools promise this. This study asked four practical questions about them:

1. Do they report the right lines?
2. Do they change how the program behaves while measuring it?
3. How much do they slow a test run?
4. Can you still use the Godot Editor's debugger while they are on?

Every answer below comes from running the real tools against Godot 4.7.1 with hand-checked expected results, not from the tools' own documentation or self-reports. Where a question could not be answered, the report says so rather than guessing.

## The tools

Three tools were considered. Two could be tested; one could not.

| Tool | Version | Test runner it works with | Setup experience |
| --- | --- | --- | --- |
| gd-tools | 0.4.0 | GUT 9.7.1 | Installed from PyPI with no problems. |
| Nano Coverage | commit fce7a0ae (June 2026, the latest available) | GdUnit4 6.2.1 | Had to be compiled from source, and its build config names the output file wrongly, which needed a manual workaround. Its documented command-line mode crashes; only its GdUnit4 integration works. |
| godot-code-coverage | latest commit | GUT | Excluded. It is silently broken on Godot 4.7.1: tests run and pass, but no coverage file is ever written. |

All tests ran on Godot 4.7.1 (the official Linux build) on a single 16-core Intel laptop running Linux, with the CPU locked to full speed and nothing else running.

## How accurate is the coverage they report?

Both tools were run against 53 small, hand-written test programs whose correct coverage was worked out by hand and reviewed independently before any tool saw them. Each discrepancy was traced to its root cause in the tool's own code, so the numbers below count causes, not symptoms.

**gd-tools got 13 of 53 wrong, from 4 causes:**

- Its "branch taken" counter fires whenever a condition is *checked*, not when the branch is actually *taken*. An `if` whose body never runs can still show as 100% covered. This is the most serious finding for gd-tools.
- One-line conditionals (`x if cond else y`) get no branch tracking at all.
- It cannot tell "this branch was never reached" from "this branch was reached and skipped".
- Three kinds of declaration line are not tracked at all.

**Nano Coverage got 6 of 53 wrong, from 3 causes:**

- Property getter and setter bodies are completely missing from its output, even when they run.
- In a `match` statement, patterns that did not match are omitted from the report entirely, rather than shown as unreached.
- An `elif` that was checked but not taken shows as if it was never reached at all.

The checker itself was tested with deliberately wrong answers to confirm it can fail; it did, every time. So the short finding list is a real result, not a broken test.

**Do they change your program's behavior?** No evidence that they do. Tests produced identical results with and without coverage across every case checked. One caveat on the test-runner side: GUT reports success even when it finds zero tests to run, so a passing run is not proof that anything was measured. This study's own harness was caught by that exact trap once and had to be fixed.

**Not tested:** a group of cases covering Godot's node lifecycle (scene enter, ready, exit) was only spot-checked, not run in full.

## How much does coverage slow your tests?

It depends almost entirely on what the code does. Three representative workloads were each tuned to about two seconds of real work, then run 60 times per tool per condition (1,200 runs in total, over 3.7 hours, with the machine checked for idleness before every session).

**How much slower with coverage on.** Work time with coverage divided by work time without, on identical fixed work. Estimates from 10 sessions with 95% intervals; a value of 1 means no slowdown.

| Workload | gd-tools | Nano Coverage |
| --- | --- | --- |
| Branch-heavy logic | 12.4x [12.3, 12.5] | 9.7x [9.6, 9.8] |
| Scene application | 4.5x [4.5, 4.5] | 3.7x [3.7, 3.7] |
| Signal dispatch | 1.06x [1.05, 1.06] | 3.0x [2.9, 3.0] |

Tight loops full of `if` statements slow down by about ten times under either tool. A typical scene with state, signals, and resource loads slows by about four times. Signal dispatch is nearly free under gd-tools but three times slower under Nano Coverage.

The percentage view flatters gd-tools on the branch-heavy workload. Each tool has a different fixed startup cost, so the fairer comparison is how many seconds each one adds to the same work:

**Seconds added by coverage** on about 2 seconds of identical work.

| Workload | gd-tools | Nano Coverage |
| --- | --- | --- |
| Branch-heavy logic | +22.2s | +17.1s |
| Scene application | +6.1s | +4.7s |
| Signal dispatch | +0.1s | +3.8s |

On the branch-heavy workload gd-tools adds more time in absolute terms despite its smaller ratio. On the signal workload the picture reverses.

Two more findings: installing gd-tools but leaving coverage switched off costs nothing measurable, and on an empty application either tool adds well under a fifth of a second to the whole run. None of the 1,200 runs failed, timed out, or was excluded from these numbers.

## Does it break the debugger?

Partly, and in the same way for both tools.

Both tools measure coverage by rewriting each script in memory, inserting an extra line of bookkeeping code before each statement they want to count, just before Godot compiles it. Godot has no way to know those lines are not the original source. So when a script hits an error, every line number Godot reports is pushed down by the number of inserted lines above it.

This was confirmed by attaching directly to Godot's debugger connection, the same one the Editor's Debugger panel uses. A division by zero on line 4 of a four-line file is reported on line 5 by both tools, in the debugger as well as in the console. In a real file with many tracked statements, the drift grows the further down the file the error is. A developer reading the Debugger panel during a covered test run will be sent to the wrong line.

**What was not verified:** whether a breakpoint you set yourself, in the Editor's gutter, still stops on the line you meant. The minimal debugger client built for this study could not activate manual breakpoints (real clients evidently send configuration this study did not reverse-engineer), and a live Editor session was not available in the test environment. This is an open question, not a confirmed defect.

Neither tool shows coverage inside the Editor. Both produce an external report only: an HTML page for gd-tools, an LCOV file for Nano Coverage.

## What this study does not tell you

- **Other machines.** Everything ran on one Linux laptop in one afternoon. This was a deliberate choice, not an accident, but it means the timings are specific to that hardware. The ratios between conditions are more portable than the raw seconds.
- **Why coverage costs what it costs.** The study measured the slowdown precisely but did not profile inside Godot to attribute it to specific operations. Linux `perf` was not available on the test machine.
- **Memory and CPU time.** Only wall-clock time was measured.
- **Real projects.** The workloads are synthetic. No real game was tested.
- **Fair comparison of accuracy across tools.** gd-tools tracks branches and Nano Coverage does not, so they are not doing identical work. gd-tools runs headless while Nano Coverage's runner opens a window. Percentages between the two are not directly comparable; seconds added are closer.
- **Manual breakpoints** under coverage, as noted above.
- **Statistical caveats.** Ten sessions per measurement is enough to estimate each effect well, but the intervals are per-measurement, not adjusted for reading many at once. One measurement (gd-tools on the branch-heavy workload) drifted about 1.5% across the afternoon, which is small against a 12x effect but is noted rather than hidden.

Every number in this report was regenerated from the raw data files and compared byte-for-byte against the committed report before publishing. That is a same-machine check; nobody else has yet reproduced the results independently.

## Recommendation

**Do not build a new coverage tool.** Nothing found here requires one. Both existing tools do the core job; their defects are specific and fixable.

**Report the defects upstream, with this test corpus attached.** A factual write-up for each maintainer has been drafted ([maintainer-review-package.md](maintainer-review-package.md)), with reproduction commands and suggested wording. Nothing has been sent; that is the project owner's call.

**The one architectural lesson** is shared by both tools: rewriting source text before Godot compiles it, with no map back to the original lines, is what breaks every line number afterward, including in the debugger. Any future fix, in either tool or elsewhere, should either instrument without rewriting the source or keep a line map and translate diagnostics through it.

**For a Godot developer choosing today:** gd-tools installs more easily and tracks branches, but its branch counter overcounts; Nano Coverage's per-line accuracy is slightly better but it must be built from source and misses getters and setters. Either is usable if you know the caveats above. Neither should be trusted for line-exact claims or for error line numbers while coverage is switched on.
