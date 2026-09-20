# BP05: Nano Coverage vs. Godot 4.7.1

Part of [BP05](../../../docs/benchmarks/implementation-plan.md). See
[../../candidates/nano-coverage-godot-PIN.md](../../candidates/nano-coverage-godot-PIN.md)
for the full build log, exact commit, and all findings -- this directory is
just the reproduction fixture for finding #4 there (the documented headless
memory-instrumentation API crashes).

## Reproduce

The `addons/nano_coverage_godot/` directory here is **not committed**
(gitignored -- see repo `.gitignore`) because it contains the compiled
GDExtension `.so` files. To reproduce:

1. Build Nano Coverage per `nano-coverage-godot-PIN.md`'s exact commands
   (`target=template_debug` is sufficient for this headless case).
2. Copy `demo/addons/nano_coverage_godot/` from that build into
   `addons/nano_coverage_godot/` here.
3. Copy (don't rename, to preserve both names for inspection) each built
   `.so` to drop the `lib` prefix the checked-in `.gdextension` file expects
   (see PIN.md finding #1).
4. `godot --headless --path . --import`
5. `godot --headless --path . --script driver.gd`

Expected result: instrumentation succeeds ("Scripts Patched Successfully: 2"),
then `SCRIPT ERROR: Cannot call method 'hit' on a null value.` when the
instrumented `Subject.run(3)` executes -- exactly reproducing the
documented-API crash in PIN.md's finding #4.
