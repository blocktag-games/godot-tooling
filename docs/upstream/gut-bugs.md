# GUT bugs to report upstream

Twelve independent defects found while reading `bitwes/Gut`'s source as a
candidate coverage/test-runner adapter (see the [tooling
survey](../research/2026-09-06-godot-tooling-survey.md) and [first
executable slice](../benchmarks/implementation-plan.md#first-executable-slice),
which starts adapter evaluation with gd-tools/GUT). None of these currently
have an open issue against `bitwes/Gut` — checked the full open+closed issue
list on 2026-09-19; the closest existing issues (#849, #785, #733, #772,
#803) are adjacent (same subsystem) but distinct defects, not duplicates.

None of these are blockers for evaluating GUT as an adapter candidate: every
one below is either unreachable from ordinary usage, editor-only, or affects
a code path this project's own benchmark work does not yet exercise (GUT
doubling/stubbing, `PackedVector4Array` assertions, three-or-more-default
method signatures). They're tracked here so they aren't lost, and so a PR
against upstream is a small, well-scoped first open-source contribution once
BP04/BP05 (the GUT adapter work) is underway.

Status column: **unfiled** (no GitHub issue yet), **filed** (issue open),
**PR** (issue + pull request open), **merged** (upstream fixed).

| # | Bug | File | Status |
| --- | --- | --- | --- |
| 1 | Track Errors checkbox negates the control object, not `.value` | `addons/gut/gui/gut_config_gui.gd:240` | unfiled |
| 2 | Vendored pin is one patch release behind (9.7.0 vs 9.7.1) | `addons/gut/plugin.cfg` | n/a — pin decision, not a bug |
| 3 | `GutUtils.DoubleTools` calls nonexistent `get_loader()` | `addons/gut/utils.gd:107` | unfiled |
| 4 | Missing `return` in `get_panel_shortcut()` | `addons/gut/gui/GutBottomPanel.gd:562-563` | unfiled |
| 5 | Inverted `disable_menu("run_test", ...)` call | `addons/gut/gui/RunAtCursor.gd:94` | unfiled |
| 6 | `UserFileViewer` sets a Godot-3 `window_title` property | `addons/gut/UserFileViewer.gd:31` | unfiled |
| 7 | Missing `TYPE_PACKED_VECTOR4_ARRAY` entry in the type table | `addons/gut/strutils.gd:9-47` | unfiled |
| 8 | `gut_plugin`'s `_exit_tree` isn't null-guarded on one skipped-init path | `addons/gut/gut_plugin.gd:140` | unfiled |
| 9 | `RunResults` reads `.pressed` (a signal) instead of `.button_pressed` | `addons/gut/gui/RunResults.gd:83` | unfiled |
| 10 | `ParsedMethod`'s default-argument index arithmetic is backwards | `addons/gut/script_parser.gd:34` | unfiled |
| 11 | `check_for_update`'s mouse-exit handler resets the wrong variable twice | `addons/gut/gui/check_for_update.gd:150-152` | unfiled |
| 12 | `-gerrors_do_not_cause_failure` CLI flag's value is parsed but dropped | `addons/gut/cli/gut_cli.gd:122,173` | unfiled |

## Details

### 1. Track Errors checkbox negates the control object, not `.value`

`get_options` (`addons/gut/gui/gut_config_gui.gd:240`) builds
`to_return.no_error_tracking = !_cfg_ctrls.error_tracking` — negating the
`BooleanControl` object itself rather than its `.value`, unlike every
sibling line in the same block (e.g. `.error_tracking.value`). A non-null
Object is always truthy in GDScript, so the expression is constantly
`false`; the panel's "Track Errors" checkbox can never write
`no_error_tracking=true`. Fix: `!_cfg_ctrls.error_tracking.value`.

### 2. Vendored pin is one patch release behind

Not a bug — a version-currency question. 9.7.1 fixes upstream issues #841
and #842, both confined to double generation. Relevant if/when this
project's GUT adapter work starts exercising doubling/stubbing.

### 3. `GutUtils.DoubleTools` calls nonexistent `get_loader()`

The static property getter at `addons/gut/utils.gd:107` reads
`get: return DoubleTools.get_loader()`, but `LazyLoader`'s accessor is
`get_loaded` (`addons/gut/lazy_loader.gd:32`) — every other lazy-loaded
`GutUtils` property uses the correct name. Reading `GutUtils.DoubleTools`
raises "Invalid call. Nonexistent function `get_loader` in base
`RefCounted`." Fix: rename the call to `get_loaded()`.

### 4. Missing `return` in `get_panel_shortcut()`

`get_panel_shortcut` (`addons/gut/gui/GutBottomPanel.gd:562-563`)
evaluates `_ctrls.shortcut_dialog.scbtn_panel.get_shortcut()` with no
`return`, so it always yields `null`. Its only caller,
`gut_plugin.gd:120`, assigns that `null` as the dock's shortcut, so a
configured "Show/Hide GUT" shortcut never reaches the dock. Editor-only.
Fix: add the missing `return`.

### 5. Inverted `disable_menu("run_test", ...)` call

`_update_buttons` (`addons/gut/gui/RunAtCursor.gd:90-95`) disables three
menu entries with the negation of a presence flag, but line 94 passes the
flag itself: `menu_manager.disable_menu("run_test", is_test_method)`.
Per the `(menu_name, disabled)` contract this disables "Run Test" exactly
when it's usable and enables it otherwise — backwards from every sibling
call in the function. Fix: negate the flag, matching the other three
calls.

### 6. `UserFileViewer` sets a Godot-3 `window_title` property

`show_file` assigns `self.window_title = path`
(`addons/gut/UserFileViewer.gd:31`) on a `Window` node. Godot 4's
`Window` exposes `title`, not `window_title`; the assignment raises
"Invalid assignment of property or key." Likely dead code upstream too —
worth checking if anything in `bitwes/Gut` itself instantiates this
scene before filing. Fix: `self.title = path`.

### 7. Missing `TYPE_PACKED_VECTOR4_ARRAY` entry in the type table

`GutStringUtils.types` (`addons/gut/strutils.gd:9-47`) enumerates 38
`TYPE_*` constants but omits `TYPE_PACKED_VECTOR4_ARRAY`, which GUT's own
`gut_constants.gd:42` lists. Three call sites index the table without a
`has()` guard (`comparator.gd:9-10`, `test.gd:1336`, `test.gd:192-198`),
so an assertion comparing a `PackedVector4Array` produces an "Invalid
access to key" engine error instead of GUT's intended readable
datatype-mismatch failure. Fix: add the missing table entry, and
consider hardening the three unguarded indexers with `.get(..., 'UNKNOWN')`.

### 8. `gut_plugin`'s `_exit_tree` isn't null-guarded on one skipped-init path

`_exit_tree` calls `_check_for_update.queue_free()` unconditionally
(`addons/gut/gut_plugin.gd:140`), but `_check_for_update` is initialized
only inside `_should_continue_loading_gut`, which `_enter_tree` skips
entirely when `_version_conversion()` returns false (the documented
"restart the editor or run `godot --headless --import`" state). In that
state `_check_for_update` is still null at teardown and the call raises.
The two statements above it already have null guards. Fix: wrap the call
the same way — `if(_check_for_update != null): _check_for_update.queue_free()`.

### 9. `RunResults` reads `.pressed` (a signal) instead of `.button_pressed`

`_open_script_in_editor` branches on
`if(_ctrls.toolbar.show_script.pressed)` (`addons/gut/gui/RunResults.gd:83`).
On a Godot 4 `BaseButton`, `pressed` is a signal (always truthy), not the
toggle state — `button_pressed` is, and the same control is read
correctly as `.button_pressed` twelve lines later. The branch is
therefore always taken, so clicking a result always jumps to the Script
screen regardless of the "Sync: script" toggle. Fix: read
`.button_pressed`, matching the other call site.

### 10. `ParsedMethod`'s default-argument index arithmetic is backwards

`ParsedMethod._init` records each argument's default with
`arg['default'] = _meta.default_args[start_default - i]`
(`addons/gut/script_parser.gd:34`); the correct offset is
`i - start_default`. For one or two defaults the two formulas coincide by
accident; for three or more they diverge, so parsed-signature output
(`ParsedMethod.to_s`) misreports defaults on methods with 3+ defaulted
arguments. Not reached by double generation itself (`method_maker.gd`
and `stub_params.gd` compute defaults correctly and independently) —
confined to the parsed-signature display. Fix: `arg['default'] =
_meta.default_args[i - start_default]`.

### 11. `check_for_update`'s mouse-exit handler resets the wrong variable twice

`_on_mouse_exited` (`addons/gut/gui/check_for_update.gd:150-152`)
assigns `_mouse_down = false` and then `_mouse_down = 0.0` — the same
variable twice. The second statement was evidently meant for
`_mouse_down_duration`, which the sibling mouse-up handler resets
correctly. Because the duration is never cleared on mouse-exit, a
drag-off-and-press-again sequence reaches the four-second verbose
threshold sooner than intended. Editor diagnostic gesture only. Fix:
change the second statement's target to `_mouse_down_duration`.

### 12. `-gerrors_do_not_cause_failure` CLI flag's value is parsed but dropped

The CLI advertises `-gerrors_do_not_cause_failure`
(`addons/gut/cli/gut_cli.gd:122`) and copies it to the resolver
(`:173`), but `errors_do_not_cause_failure` is not a key of
`gut_config.default_options`, and `OptionResolver.get_resolved_values`
iterates only `base_opts` (seeded from `default_options`). The value is
written and then silently dropped — never reaches `_final_opts` or
`gut_config._apply_options`'s deprecation check. An operator passing the
documented flag gets no behavior change and no diagnostic. Fix: add
`errors_do_not_cause_failure` as a key of `gut_config.default_options`,
or remove the flag from the advertised `-gh` list if it's genuinely
retired.

## Related but distinct upstream issues

Worth linking as context when filing, since they touch the same
subsystems — not duplicates of anything above:

- [#849](https://github.com/bitwes/Gut/issues/849) (closed) — the 9.7.1
  release's `plugin.cfg` reports version 9.6.0. Relevant background for
  bug 2 (the version-pin decision) but a different defect.
- [#785](https://github.com/bitwes/Gut/issues/785) (open) — errors
  between tests aren't counted.
- [#733](https://github.com/bitwes/Gut/issues/733) (closed feature
  request) — fail tests on engine error.
- [#772](https://github.com/bitwes/Gut/issues/772) (closed) —
  `assert_push_error()` doesn't skip previously handled push errors.
- [#803](https://github.com/bitwes/Gut/issues/803) (open) — error
  string on engine errors lacks the actual error message.

All four of these sit in the same error-tracking code area
(`error_tracker.gd` / `gut_config.gd`) as bug 1 and bug 12 above.

## Next step

File each as a standalone GitHub issue against `bitwes/Gut`, one PR per
issue where the fix is this small and self-contained (all twelve
qualify). Do not reference this repository, a review, or any internal
tracking id in the upstream report — it should stand on its own. Record
each issue/PR URL back into this file's status column once filed.
