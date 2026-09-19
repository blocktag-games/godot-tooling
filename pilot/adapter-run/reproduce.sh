#!/usr/bin/env bash
# BP04: literal one-command reproduction for an adapter-run case.
#
# Restores the gitignored addons/ directory (GUT + gd-tools-coverage,
# both reproducible from what's already committed elsewhere in this
# repo rather than downloaded again), builds the project's import
# cache, runs the real `gd-tools test --coverage`, and finally runs
# the case's compare.py against the freshly generated artifacts --
# not artifacts left over from a previous run.
#
# Usage: pilot/adapter-run/reproduce.sh f010_straight_line
#        pilot/adapter-run/reproduce.sh f020_if_both_outcomes
set -euo pipefail

if [ $# -ne 1 ]; then
	echo "usage: $0 <case-dir-name>" >&2
	exit 2
fi

CASE_NAME="$1"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
CASE_DIR="$HERE/$CASE_NAME"
GODOT_BIN="$REPO_ROOT/pilot/godot/Godot_v4.7.1-stable_linux.x86_64"
GD_TOOLS_BIN="$REPO_ROOT/pilot/gd-tools/.venv/bin/gd-tools"
GD_TOOLS_SITE_PACKAGES="$REPO_ROOT/pilot/gd-tools/.venv/lib/python3.13/site-packages/gd_tools"
GUT_SOURCE="$REPO_ROOT/pilot/fixtures/cases/f064_zero_requested_tests/addons/gut"

if [ ! -d "$CASE_DIR" ]; then
	echo "no such case: $CASE_DIR" >&2
	exit 2
fi
if [ ! -x "$GODOT_BIN" ]; then
	echo "pinned Godot binary not found at $GODOT_BIN -- see docs/benchmarks/pilot-environment.md" >&2
	exit 2
fi
if [ ! -x "$GD_TOOLS_BIN" ]; then
	echo "gd-tools not installed -- run 'pipenv sync' in pilot/gd-tools/ first" >&2
	exit 2
fi

echo "==> Restoring addons/ into $CASE_NAME"
rm -rf "$CASE_DIR/addons"
mkdir -p "$CASE_DIR/addons"
cp -r "$GUT_SOURCE" "$CASE_DIR/addons/gut"
cp -r "$GD_TOOLS_SITE_PACKAGES/addons/gd-tools-coverage" "$CASE_DIR/addons/gd-tools-coverage"

echo "==> Clearing prior .godot import cache and .gd-tools evidence"
rm -rf "$CASE_DIR/.godot" "$CASE_DIR/.gd-tools"

echo "==> Building import cache"
export GODOT_BIN
"$GODOT_BIN" --headless --path "$CASE_DIR" --import > /dev/null 2>&1

echo "==> Running gd-tools test --coverage"
(cd "$CASE_DIR" && "$GD_TOOLS_BIN" test --coverage)

echo "==> Comparing against oracle"
(cd "$CASE_DIR" && python3 compare.py)
