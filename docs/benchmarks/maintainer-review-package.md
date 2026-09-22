# Maintainer review package

Factual review material for gd-tools-cli and Nano Coverage maintainers, per `publication-plan.md`'s "Fair comparison and review" requirement: pinned version, exact commands, expected vs. actual behavior, relevant logs, and draft wording. **Preparing this material is part of the study. Sending it — opening an issue, emailing a maintainer — is a separate action requiring the project owner's explicit authorization, which has not been given as of this document's date.** Nothing here has been sent anywhere.

Maintainers do not need to endorse this study's conclusions for it to stand; feedback that corrects a setup error or clarifies an intended contract is welcome and would be recorded as an amendment, not silently folded into the original findings.

---

## gd-tools-cli 0.4.0

**Pinned version:** `v0.4.0`, commit `b5044c33e2928dad9c21c0d908bc799e33a25c34`. Godot 4.7.1-stable (`4.7.1.stable.official.a13da4feb`). GUT v9.7.1.

### Finding 1 — `if_true`/`elif_true`/`loop_body` counters fire on evaluation, not on the labeled outcome

**Reproduction:**
```
cd pilot/adapter-run/  # or the standalone F020 fixture directory
python3 <the F020 comparison script — see docs/benchmarks/fixture-catalog.tsv's F020 row>
gd-tools test --coverage   # against pilot/fixtures/cases/f020_if_true_false/
```
**Expected:** a branch whose *body* never executes should not read as covered under an "if_true" label.
**Actual:** the counter increments on every evaluation of the decision expression, so a branch that is always false at runtime can still report 100% under `if_true`.
**Evidence:** `pilot/fixtures/oracles/F020.json`; direct read of `coverage.gd`'s counter-injection logic, cited by path and line in that oracle file.

**Draft wording (not sent):** "Testing gd-tools-cli 0.4.0 against a minimal if/else fixture where the `if` body is provably never entered at runtime, the coverage report's `if_true` branch counter still shows the branch as reached. Reading `coverage.gd`'s instrumentation, the counter appears to be incremented when the *decision* is evaluated, not when the *labeled outcome* is taken. Is this the intended contract for `if_true` (documenting evaluation, not the true-outcome body), or a mechanism defect? Happy to share the minimal repro fixture either way."

### Finding 2 — Ternary/conditional expressions have zero branch-level tracking

**Reproduction:** a fixture with a ternary expression run under both possible outcomes; `gd-tools test --coverage`'s plan/report has no branch-level entry for either arm.
**Expected:** each arm of a conditional expression is distinguishable in the report, matching if/else treatment.
**Actual:** no trackable point exists for either arm at all — the whole expression is invisible to branch accounting.
**Evidence:** `pilot/fixtures/oracles/F029.json` and the corpus sweep's own root-cause entry (`docs/benchmarks/corpus-run-2026-09-19.md`, gd-tools finding 4).

**Draft wording (not sent):** "Ternary (`a if cond else b`) expressions don't appear to get any branch-level coverage tracking at all in our testing — is this an intentional scope limitation, or a gap worth an issue?"

### Finding 3 (already published) — F057: instrumentation shifts reported error lines by inserting tracker calls into the live source

**Reproduction:** `pilot/adapter-run/f057_instrumentation_shifts_error_lines/check.py` (fully automated, no manual steps).
**Expected:** a runtime error in an instrumented script reports the same line number a developer sees in their own unmodified source file.
**Actual:** confirmed directly: the identical script's division-by-zero reports line 4 uninstrumented and line 5 once gd-tools' real coverage plan is applied — `coverage.gd`'s `_inject_trackers()` inserts tracker-call lines into the in-memory `source_code` string before `Script.reload(true)`, and the engine has no way to know those lines aren't original, so every subsequent line-numbered diagnostic (SCRIPT ERROR, assert failure, `print_stack()`, and — newly confirmed by F082, see below — the remote debugger's own structured error report) is offset.
**Evidence:** `pilot/fixtures/oracles/F057.json`, `pilot/fixtures/oracles/F082.json`.

**Draft wording (not sent):** "We found that inserting tracker calls directly into a script's live source before `Script.reload()` shifts every subsequent line-numbered diagnostic — including what the Godot Editor's own Debugger panel shows for an unhandled error — away from the line a developer is actually looking at in their unmodified file. Would a source-map-style translation layer (original line ↔ instrumented line) be in scope for a fix, or is this a known, accepted tradeoff of the in-memory injection approach?"

---

## Nano Coverage (via GdUnit4's session hook), commit `fce7a0ae`

**Pinned version:** commit `fce7a0ae9281533456023275504bbd81d74d95be` (2026-06-13). Godot 4.7.1-stable. GdUnit4 v6.2.1.

### Finding 1 — Match-statement pattern label lines receive no LCOV record when not matched

**Reproduction:** a `match` statement with 3+ patterns, run so exactly one pattern matches; inspect `coverage-report/lcov.info` for the unmatched pattern-label lines (`1:`, `2:`, `_:`).
**Expected:** an unmatched-but-present pattern label line appears in the LCOV report as present-but-zero-hits, distinguishable from "not part of the tracked source at all."
**Actual:** unmatched pattern label lines are entirely absent from the LCOV record — indistinguishable from a line outside the tracked file.
**Evidence:** `docs/benchmarks/corpus-run-2026-09-19.md`, Nano Coverage finding 2.

**Draft wording (not sent):** "Pattern label lines in an unmatched `match` arm don't appear in the generated LCOV at all, rather than appearing as a zero-hit line. This makes it impossible to distinguish 'never reached' from 'not instrumented' from the LCOV file alone. Is this a known LCOV-export limitation?"

### Finding 2 — Property getter/setter accessor bodies are entirely absent from coverage tracking

**Reproduction:** a class with a `get`/`set` property accessor whose body is exercised via normal property read/write; the LCOV report has no entry for the accessor body at all.
**Expected:** accessor bodies are tracked like any other function body.
**Actual:** entirely untracked — a real gap in source population, not a labeling choice.
**Evidence:** `docs/benchmarks/corpus-run-2026-09-19.md`, Nano Coverage finding 3 (contract-independent).

**Draft wording (not sent):** "Property getter/setter bodies don't appear anywhere in the generated coverage report, even when exercised. Is accessor instrumentation on the roadmap, or intentionally out of scope for the current instrumentation approach?"

### Finding 3 (new, this study) — F082: coverage instrumentation also shifts reported error/debugger lines

**Reproduction:** `pilot/adapter-run/f082_debugger_error_line_accuracy/check.py` (fully automated).
**Expected:** same as gd-tools Finding 3 above.
**Actual:** confirmed directly: the identical division-by-zero fixture reports line 4 uninstrumented and line 5 once Nano Coverage's GdUnit4 session hook has run `instrument_all_scripts()` — both in raw stderr text and in Godot's own remote debug protocol's structured error message (the same data source the Editor's Debugger panel renders). Two separate parse-time `INTEGER_DIVISION` warnings are observed for the same file (at line 4 and line 5), consistent with the file being reloaded once before and once after in-memory instrumentation — the same shape F057 already established for gd-tools, though Nano Coverage's own native instrumentation code was not directly inspected to confirm an identical mechanism, only an identical symptom.
**Evidence:** `pilot/fixtures/oracles/F082.json`.

**Draft wording (not sent):** "We found the same line-shift behavior in Nano Coverage that's separately been reported for other in-memory GDScript instrumentation approaches: after `instrument_all_scripts()` runs, a runtime error in the identical unmodified source reports one line further down than an uninstrumented run — visible both in stderr and in Godot's own remote debugger protocol (i.e., what the Editor's Debugger panel would show). Happy to share the minimal repro either way — wanted to check whether this is a known tradeoff of the in-memory approach before writing it up."

---

## Both candidates — known-answer control notes

Every finding above passed this study's own known-answer control gates (deliberately planted correct AND incorrect answers used to prove the checking script itself can detect a failure) on every run in both the original and a rebuilt sweep, which reproduced byte-for-byte identical results. This is stated so a maintainer does not need to take the "no more findings than these" claim on faith — the checking methodology was itself checked.
