# BP02 tier-0 fixtures (group 1: pure GDScript)

Part of [BP02](../../docs/benchmarks/implementation-plan.md): implement the first
independent fixtures and oracles. This is group 1 of the three-group build order
in the implementation plan — cases needing only a standalone driver, no live
Godot process lifecycle and no BP03 harness.

No coverage tool touches anything here. This only establishes and verifies the
uninstrumented ground truth per [correctness-protocol.md](../../docs/benchmarks/correctness-protocol.md):
each fixture is a small GDScript program, each oracle in `oracles/` is a
hand-traced statement of exactly which lines/branches/functions execute for
which named inputs, bound to the fixture file's exact SHA-256 hash.

## Cases

| ID | Case | Files |
| --- | --- | --- |
| F001 | Never-loaded selected file | `cases/f001_never_loaded/{loaded,unloaded}.gd` |
| F002 | Never-called function | `cases/f002_never_called/subject.gd` |
| F010 | Straight-line body | `cases/f010_straight_line/subject.gd` |
| F012 | Multiline expression | `cases/f012_multiline_expression/subject.gd` |
| F020 | If with both outcomes | `cases/f020_if_both_outcomes/subject.gd` |
| F021 | If without explicit else | `cases/f021_if_without_else/subject.gd` |
| F025 | For loop zero/one/many elements | `cases/f025_for_loop_iteration/subject.gd` |

Each `subject.gd` exposes a single static entry function, called directly by
`driver.gd` — no fixture is rewritten to suit a particular collector's
integration style, per the implementation plan's constraint.

## Reproduce

From this directory, using the pinned Godot 4.7.1 binary recorded in
[pilot-environment.md](../../docs/benchmarks/pilot-environment.md):

```sh
../godot/Godot_v4.7.1-stable_linux.x86_64 --headless --path . --script driver.gd
```

Expected: every case prints `PASS`, ending with
`All tier-0 group 1 fixtures match their behavioral specification.` and exit
code 0. This is the uninstrumented baseline check from correctness-protocol.md
step 2 — it does not itself constitute a coverage measurement.

To re-verify a fixture hasn't drifted from its bound oracle:

```sh
sha256sum cases/f010_straight_line/subject.gd
# must match the "sha256" field in oracles/F010.json
```

## Status and open items

- Oracles are single-author, not yet second-reviewed (`"reviewer": null` in
  each oracle file). Per correctness-protocol.md, a second human review is
  desirable before public correctness claims.
- Groups 2 (live-process lifecycle: F040/F091/F045/F060) and 3
  (harness-dependent: F008/F062/F064/F065/F071) are not yet built — see the
  implementation plan's tier-0 build order.
- No coverage adapter has run against these fixtures. That begins in BP04,
  after BP03's harness exists.
