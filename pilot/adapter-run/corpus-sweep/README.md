# BP06: corpus sweep against gd-tools-cli 0.4.0

Runs the entire Group 1 (pure-GDScript) tier-0/tier-1 fixture corpus
through real `gd-tools test --coverage`, one invocation per oracle
input, and compares each against its oracle via
`pilot/harness/comparator.py`. This is BP06's closing evidence: "run
the corpus against viable candidates."

`results.tsv` is the output of the last real run (2026-09-19), 53 rows
(26 fixtures, one row per named oracle input). See
`docs/benchmarks/corpus-run-2026-09-19.md` for the categorized findings
this run produced.

## Why this isn't `pilot/adapter-run/reproduce.sh`

`reproduce.sh` runs ONE fixture's own dedicated adapter-run project.
This sweep instead runs `pilot/fixtures/` itself as one big Godot
project (it already has its own `project.godot`, and every fixture's
`cases/f0XX.../subject.gd` path already resolves correctly from
there), with GUT + gd-tools-coverage added, and `test_corpus.gd`
providing one test function per (fixture, oracle input) pair. Each
function is run in isolation via `gd-tools test --coverage --test
<func_name>` -- never batched, since a real coverage report is
cumulative for its own process and batching would falsely satisfy
"not yet reached" obligations with a later input's hits.

## Reproducing

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

## Scope

Covers every Group 1 (pure-GDScript, no live scene tree needed) fixture
with a built oracle -- tier-0 and tier-1, 26 fixtures, 53 inputs. Does
NOT cover:

- **Group 2 (lifecycle, own mini-projects)** -- F040-F049/F091, F060.
  These each have their own `project.godot`/driver, so they don't fit
  this sweep's shared-project shape. One (F042, enter/ready/exit-tree)
  was spot-checked by hand: gd-tools' coverage collection works
  correctly in a live scene-tree context too, all three obligations
  matched exactly. The rest are unswept -- deferred, not assumed clean.
- **Group 3 (harness-dependent, real-tool)** -- these already run
  against real tools as part of their own construction (each has its
  own `check.py`); re-running them through this generic sweep would be
  redundant, not new evidence.
- **GdUnit4 and Nano Coverage** as coverage collectors across this
  corpus -- GdUnit4 is a test *runner*, not a coverage collector (F080
  already established application-behavior parity with GUT); gd-tools'
  own coverage collection is bound to GUT's hooks and was never wired
  to GdUnit4. Nano Coverage has exactly one working integration
  (`pilot/adapter-run/nano-coverage-gdunit4-f010_straight_line/`,
  re-verified passing as part of this pass) -- extending it across the
  corpus needs a second full adapter, not built here.
