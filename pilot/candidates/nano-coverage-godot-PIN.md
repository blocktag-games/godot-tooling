# Nano Coverage (nano-coverage-godot) pin

- Upstream: https://github.com/IgorBayerl/nano-coverage-godot
- Commit: `fce7a0ae9281533456023275504bbd81d74d95be` (2026-06-13), confirmed
  via GitHub API on 2026-09-19 to be upstream's latest commit.
- License: Apache-2.0, confirmed directly against `LICENSE.md`.
- Submodules pinned (shallow, `--depth 1`, at whatever commit `.gitmodules`
  resolved to on 2026-09-19): `godot-cpp` (branch `4.3` -- the extension
  targets Godot's 4.3-era C++ API bindings, not 4.7), `thirdparty/tree-sitter`,
  `thirdparty/tree-sitter-gdscript`, `thirdparty/gdUnit4`.
- Built with `scons` 4.11.1 (installed via `pip install --user
  --break-system-packages scons`, no sudo needed) and the system `g++`.
  Built both `target=template_debug` and `target=editor`
  (`build_tests=no`), each via `python3 -m SCons target=<t> build_tests=no
  -j$(nproc)`. Both builds succeeded (exit 0) on this machine.
- Compiled binaries are NOT committed (matches this project's existing
  pattern for the Godot binary itself). Rebuild with the commands above from
  a fresh `git clone --depth 1` plus shallow submodule init per
  `.gitmodules`.

## BP05 findings

### 1. Real build-packaging bug: output filename never matches what's loaded

`SConstruct` builds the shared library via SCons' `SharedLibrary()`, which
always applies the platform's `$SHLIBPREFIX` ("lib" on Linux) to the output
filename -- `SConstruct` never clears or overrides this. So a build produces
`libnano_coverage_godot.linux.<target>.x86_64.so`, but
`nano_coverage_godot.gdextension` (checked into the repo) references
`nano_coverage_godot.linux.<target>.x86_64.so` -- **without** the `lib`
prefix. Running the addon as freshly built therefore fails outright:

```
ERROR: GDExtension dynamic library not found: 'res://addons/nano_coverage_godot/nano_coverage_godot.gdextension'.
```

Confirmed this is a real, current defect, not something specific to this
environment: verified `SConstruct` never sets `SHLIBPREFIX`, and verified
the actual built filename via `ls`. Worked around it here by copying (not
renaming, to keep both names available for inspection) each built `.so` to
the name the `.gdextension` file expects.

### 2. Once worked around: the extension loads and initializes correctly on Godot 4.7.1

```
[NanoCoverage] Editor classes registered.
[NanoCoverage] Editor plugin ready.
```

This is a genuine, positive finding: the extension was built against
`godot-cpp`'s **4.3**-branch API bindings, and it loads and runs correctly
against this project's pinned **4.7.1** engine binary. Godot's GDExtension
ABI-compatibility promise holds here across a real three-minor-version gap,
for both the `editor` and `template_debug` build targets.

### 3. `godot --headless --path . --import` crashed (core dump) once, not deeply investigated

One `--import` run with the extension installed exited with a core dump
(`timeout: the monitored command dumped core`, exit 102) after visibly
completing several import steps including "loading_editor_layout ... DONE".
A subsequent `--import` run (after the filename fix) completed without
crashing. Not reproduced a second time under the same conditions, and not
investigated further given time already spent -- recorded as an observed
instability, not a confirmed reproducible defect.

### 4. The documented headless/CI memory-instrumentation API crashes with a null reference

The project's own `coverage_api_example.gd` (referenced directly by the
README as "the reference if you are building ... a CI/CD pipeline script")
documents this exact sequence:

```gdscript
var bootstrapper = ProjectBootstrapper.new()
bootstrapper.instrument_all_scripts()
# ... run your code ...
Engine.get_singleton("NanoCoverage").save_session("...")
```

Reproduced via `pilot/adapter-run/nano-coverage-f010_straight_line/driver.gd`
against F010's unmodified `subject.gd`. `instrument_all_scripts()` succeeds
and reports patching 2 files. But calling the instrumented `Subject.run(3)`
immediately crashes:

```
SCRIPT ERROR: Cannot call method 'hit' on a null value.
          at: _initialize (res://driver.gd:13)
```

Reading `runtime/coverage_autoload.gd`'s doc comment shows why: it says a
`CoverageRuntime`-derived autoload is "auto-registered by NanoCoverage while
disk instrumentation is active" and "flushes ... hits ... when the game
exits" -- implying memory-mode instrumentation, run outside the full
editor-plugin-loaded context (which normally registers this runtime via
`plugin.gd`'s `_enter_tree()`), has no runtime object for injected `hit()`
calls to call into. The documented example script never mentions needing to
set this up manually. Whether this is a documentation gap (a manual runtime
setup step the example omits) or a genuine defect in the memory-mode path
outside the editor plugin's lifecycle was not resolved -- doing so would
mean reverse-engineering the C++ source's exact initialization contract,
which is out of scope for this pass's time budget.

## What this does and doesn't establish

- Nano Coverage's disk-instrumentation mode (its flagship, "no test
  framework needed" feature) was **not tested** -- it requires toggling an
  editor UI button, and a headless-equivalent path was not identified in
  the time available. This is the single most important untested surface
  for this candidate, since it's advertised as needing no test-framework
  integration.
- The GdUnit4 integration (the only currently-shipped test-framework
  integration) was **not tested** -- GdUnit4 itself wasn't installed in this
  pass. Testing Nano Coverage's memory mode via a real GdUnit4 session
  (rather than the raw `ProjectBootstrapper` call this pass used) is a
  distinct, cheaper next step, since the GdUnit4 session hook may perform
  the runtime setup step `coverage_api_example.gd` appears to skip.
- Per BP01's setup-effort budget: build and load succeeded; the
  memory-instrumentation runtime path did not, using the tool's own
  documented reference script. Recorded and moving on rather than
  continuing to debug indefinitely.
