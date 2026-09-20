# BP06: corpus sweep against candidate tools

Runs the Group 1 (pure-GDScript) tier-0/tier-1 fixture corpus through
real coverage tools -- gd-tools-cli 0.4.0 and Nano Coverage (via its
GdUnit4 session hook), the two real coverage-COLLECTING candidates
BP05 identified -- one invocation per oracle input, and compares each
against its oracle via `pilot/harness/comparator.py`. This is BP06's
closing evidence: "run the corpus against viable candidates."

Two scripts, two tools:

- `run_sweep.py` -- gd-tools-cli 0.4.0, driven through GUT. Output:
  `results.tsv`.
- `run_sweep_nano.py` -- Nano Coverage, driven through GdUnit4's
  session hook. Output: `results_nano.tsv`.

See `docs/benchmarks/corpus-run-2026-09-19.md` for the categorized
findings both runs produced.

## Before trusting a result: known-answer controls

Both scripts call a `verify_controls()` function FIRST, before writing
a single sweep row, and raise immediately if it fails -- this is a gate
in the code, not a paragraph asking a human to eyeball two cases. This
exists because it already caught a real bug: an earlier version of
`run_sweep.py` accepted any GUT run whose stdout contained the
substring `"1 passed"`, which GUT's own `0/1 passed.` FAILURE line also
contains -- the check could never fail, and 53 rows were written and
committed before that was noticed. A control gate that runs the same
comparison logic against a known answer BEFORE the sweep loop turns
"the data is probably fine because the reasoning holds" into "the data
is fine because the harness just proved it against a fact we already
had independently."

- `run_sweep.py`'s controls: F010/default must compare clean (no
  branches, a trivial positive control), and F020/value_lte_0 must
  reproduce BP04's already-independently-confirmed `false_hit` on line
  5 (gd-tools' `if_true` counter fires even though the true branch
  wasn't taken) -- a negative control that only passes if the harness
  can still find a defect it has found before.
- `run_sweep_nano.py`'s controls: the same F010 positive control, plus
  a "filter is load-bearing" control -- F020/value_lte_0 has a branch
  obligation Nano Coverage cannot possibly satisfy (it tracks no
  branches at all); comparing WITHOUT excluding it must NOT be clean,
  and comparing WITH the exclusion must be clean. This proves the
  branch-obligation filter actually removes something real rather than
  being a no-op that would make every `excluded_branch_obligations`
  count in the report fiction.

If you change either script's translation logic, run it and confirm
both controls still print `CONTROL OK` before trusting anything else
it prints.

## Why this isn't `pilot/adapter-run/reproduce.sh`

`reproduce.sh` runs ONE fixture's own dedicated adapter-run project.
This sweep instead runs `pilot/fixtures/` itself as one big Godot
project (it already has its own `project.godot`, and every fixture's
`cases/f0XX.../subject.gd` path already resolves correctly from
there), with the tool's own addon(s) added, and a generated test suite
providing one entry point per (fixture, oracle input) pair. Each is run
in isolation -- never batched, since a real coverage report is
cumulative for its own process and batching would falsely satisfy "not
yet reached" obligations with a later input's hits.

## Reproducing: gd-tools (`run_sweep.py`)

```sh
REPO_ROOT=/home/wade/code/godot-tooling
SCRATCH=/tmp/corpus-run/fixtures   # or wherever; never run this against
                                    # the real pilot/fixtures/ in place,
                                    # it adds addons/ and a tests/ dir

rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
cp -r "$REPO_ROOT/pilot/fixtures/." "$SCRATCH/"
rm -rf "$SCRATCH/oracles"

mkdir -p "$SCRATCH/addons" "$SCRATCH/tests"
cp -r "$REPO_ROOT/pilot/fixtures/cases/f064_zero_requested_tests/addons/gut" "$SCRATCH/addons/gut"
cp -r "$REPO_ROOT/pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools/addons/gd-tools-coverage" "$SCRATCH/addons/gd-tools-coverage"
cp "$REPO_ROOT/pilot/adapter-run/corpus-sweep/test_corpus.gd" "$SCRATCH/tests/test_corpus.gd"

cat >> "$SCRATCH/project.godot" << 'EOF'

[editor_plugins]

enabled=PackedStringArray("res://addons/gut/plugin.gd")

[autoload]

_GDTCoverage="*res://addons/gd-tools-coverage/coverage.gd"
EOF

export GODOT_BIN="$REPO_ROOT/pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
"$GODOT_BIN" --headless --path "$SCRATCH" --import

# Then edit run_sweep.py's SCRATCH constant to match, and:
python3 "$REPO_ROOT/pilot/adapter-run/corpus-sweep/run_sweep.py"
```

## Reproducing: Nano Coverage (`run_sweep_nano.py`)

Requires Nano Coverage already built per
`pilot/candidates/nano-coverage-godot-PIN.md` (both `.so` naming
variants present in `demo/addons/nano_coverage_godot/bin/`).

```sh
REPO_ROOT=/home/wade/code/godot-tooling
SCRATCH=/tmp/corpus-run/fixtures_nano

rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
cp -r "$REPO_ROOT/pilot/fixtures/." "$SCRATCH/"
rm -rf "$SCRATCH/oracles"

mkdir -p "$SCRATCH/addons" "$SCRATCH/test"
cp -r "$REPO_ROOT/pilot/candidates/gdUnit4/addons/gdUnit4" "$SCRATCH/addons/gdUnit4"
cp -r "$REPO_ROOT/pilot/candidates/nano-coverage-godot/demo/addons/nano_coverage_godot" "$SCRATCH/addons/nano_coverage_godot"
cp "$REPO_ROOT/pilot/adapter-run/corpus-sweep/test_nano/"*.gd "$SCRATCH/test/"

cat >> "$SCRATCH/project.godot" << 'EOF'

[editor_plugins]

enabled=PackedStringArray("res://addons/nano_coverage_godot/plugin.cfg", "res://addons/gdUnit4/plugin.cfg")

[gdunit4]

hooks/session_hooks=Dictionary[String, bool]({
"res://addons/nano_coverage_godot/integrations/gdunit_hook.gd": true
})

[nano_coverage]

integrations/gdunit4=true
EOF

export GODOT_BIN="$REPO_ROOT/pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
"$GODOT_BIN" --headless --path "$SCRATCH" --import

# Then edit run_sweep_nano.py's SCRATCH constant to match, and:
python3 "$REPO_ROOT/pilot/adapter-run/corpus-sweep/run_sweep_nano.py"
```

`test_nano/*.gd` is 53 single-function GdUnitTestSuite files, one per
(fixture, input) pair, translated from `test_corpus.gd`'s GUT assertion
style (`assert_eq(a, b)` -> `assert_that(a).is_equal(b)`). GdUnit4's CLI
(`runtest.sh`) has no test-NAME include filter -- only an ignore-list
filter (`-i`) and a fixed-path `-a <directory|path of testsuite>` --
confirmed directly by running `-help` and by `-a <suite>:<test>` being
rejected as "does not exist". One function per suite FILE, `-a
test/<file>.gd` per invocation, matches the pattern already proven
working in `nano-coverage-gdunit4-f010_straight_line/`.

Nano Coverage's LCOV output (`coverage-report/lcov.info`) is directly
keyed by real source line number (`DA:<line>,<count>`) and, per a real
disk-instrumentation run, contains an `SF:` record for every GDScript
file discovered in the whole project on that run -- not just the file
the specific test touched. `run_sweep_nano.py`'s `parse_lcov()` matches
the `SF:` record whose path ends with the oracle's own file path, per
file the fixture's obligations reference (most fixtures bind one file;
F001 and F049 bind two -- an earlier version of this script only ever
built one file's worth of `actual` data and silently mis-scored the
second file as `missing_files`, caught by reading the raw `lcov.info`
directly and seeing a correct `SF:` record for both files before
trusting the aggregate diff).

## Scope

Covers every Group 1 (pure-GDScript, no live scene tree needed) fixture
with a built oracle -- tier-0 and tier-1, 26 fixtures, 53 inputs -- for
BOTH candidates. Does NOT cover:

- **Group 2 (lifecycle, own mini-projects)** -- F040-F049/F091, F060.
  These each have their own `project.godot`/driver, so they don't fit
  this sweep's shared-project shape. One (F042, enter/ready/exit-tree)
  was spot-checked by hand against gd-tools: coverage collection works
  correctly in a live scene-tree context too, all three obligations
  matched exactly. Not spot-checked against Nano Coverage. The rest are
  unswept for either tool -- deferred, not assumed clean.
- **Group 3 (harness-dependent, real-tool)** -- these already run
  against real tools as part of their own construction (each has its
  own `check.py`); re-running them through this generic sweep would be
  redundant, not new evidence.
- **A third coverage-collecting candidate** -- there isn't one in
  BP05's survey. godot-code-coverage was excluded in BP05 for a
  verified, reproducible incompatibility with the pinned Godot 4.7.1
  engine, within the plan's own one-working-day setup budget. GdUnit4
  is a test *runner*, not an independent coverage collector (F080
  already established application-behavior parity with GUT as a
  runner, not coverage parity) -- gd-tools' own coverage collection is
  bound to GUT's hooks and was never wired to GdUnit4 as a collector.
  This is a closed question, not a deferred one: nothing found during
  this sweep reopens it.
