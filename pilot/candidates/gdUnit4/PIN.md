# GdUnit4 pin

- Upstream: https://github.com/MikeSchulze/gdUnit4
- Release: `v6.2.1` (2026-08-20T11:42:50Z), confirmed via GitHub API on
  2026-09-19 to be the current latest release.
- Commit: `08ffc7c65b61b1b2edd545616061a99973c13ce1`
- License: MIT (see `addons/gdUnit4/LICENSE`)
- Vendored: only `addons/gdUnit4/{bin,src,plugin.cfg,plugin.gd,LICENSE,
  runtest.sh,runtest.cmd}` -- the reusable runtime and CLI runner (8.5MB).
  GdUnit4's own test suite and documentation (72MB total upstream) are not
  vendored.

## BP05 result: works cleanly on Godot 4.7.1

```sh
GODOT_BIN=<pinned Godot 4.7.1 binary> bash addons/gdUnit4/runtest.sh -a test
```

Real, positive finding: ran F010's unmodified `subject.gd` through a real
GdUnit4 test (`assert_int(Subject.run(3)).is_equal(7)`) against the pinned
Godot 4.7.1 binary. 1/1 test cases passed, exit code 0, HTML and XML reports
generated. See `pilot/adapter-run/gdunit4-f010_straight_line/` for the
fixture.

The `runtest.sh` wrapper connects to `tcp://127.0.0.1:0` as its remote
debugger address and logs a connection error for it -- this is intentional
per the script's own comment ("Port 0 is used intentionally as it is never
bound... prevents Godot from activating its local interactive CLI debugger"),
not a real failure.

This closes BP05's "add a GdUnit4 driver" item. Not yet tested: GdUnit4's
own coverage-adjacent features (scene runner, fuzzing) or pairing it with
Nano Coverage's memory-mode integration (see
`nano-coverage-godot-PIN.md`'s finding 4 -- GdUnit4's session hook may
perform the runtime setup that finding's raw `ProjectBootstrapper` call
skipped; untested here, candidate BP06 follow-up).
