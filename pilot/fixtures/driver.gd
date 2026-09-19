extends SceneTree
## Standalone uninstrumented driver for the BP02 tier-0 fixtures.
##
## Runs each fixture's entry point with its named inputs and checks the
## result against the behavioral specification recorded in oracles/*.json.
## This validates step 2 of the correctness protocol (uninstrumented
## baseline behavior) before any coverage tool is involved. No coverage
## measurement happens here — that starts in BP04.

var failures: Array[String] = []


func _check(case_id: String, description: String, actual, expected) -> void:
	if actual == expected:
		print("PASS %s: %s" % [case_id, description])
	else:
		var msg := "FAIL %s: %s (expected %s, got %s)" % [
			case_id, description, str(expected), str(actual)
		]
		print(msg)
		failures.append(msg)


func _initialize() -> void:
	# F001: never-loaded selected file. Only loaded.gd is ever referenced;
	# unloaded.gd's presence in the case directory is what makes it part of
	# the selected source population without ever being loaded by anything.
	var f001 = load("res://cases/f001_never_loaded/loaded.gd")
	_check("F001", "loaded.gd.run()", f001.run(), 42)

	# F002: never-called function. Only `called` is invoked; `never_called`
	# stays declared but unreached.
	var f002 = load("res://cases/f002_never_called/subject.gd")
	_check("F002", "subject.gd.called()", f002.called(), 1)

	# F010: straight-line body, no branches.
	var f010 = load("res://cases/f010_straight_line/subject.gd")
	_check("F010", "run(3)", f010.run(3), 7)

	# F012: multiline expression: statement obligation anchored to its first
	# physical line per the oracle's documented line convention.
	var f012 = load("res://cases/f012_multiline_expression/subject.gd")
	_check("F012", "run(1, 2, 3)", f012.run(1, 2, 3), 6)

	# F020: if/else with both outcomes; two runs cover both branches.
	var f020 = load("res://cases/f020_if_both_outcomes/subject.gd")
	_check("F020", "run(2) true branch", f020.run(2), 1)
	_check("F020", "run(-2) false branch", f020.run(-2), -1)

	# F021: if without explicit else; the implicit untaken path is a
	# defined outcome, not an error.
	var f021 = load("res://cases/f021_if_without_else/subject.gd")
	_check("F021", "run(5) taken", f021.run(5), 5)
	_check("F021", "run(-5) untaken", f021.run(-5), 0)

	# F025: for loop with zero, one, and many elements.
	var f025 = load("res://cases/f025_for_loop_iteration/subject.gd")
	_check("F025", "run([]) zero iterations", f025.run([]), 0)
	_check("F025", "run([10]) one iteration", f025.run([10]), 10)
	_check("F025", "run([1, 2, 3]) many iterations", f025.run([1, 2, 3]), 6)

	print("")
	if failures.is_empty():
		print("All tier-0 group 1 fixtures match their behavioral specification.")
		quit(0)
	else:
		print("%d failure(s):" % failures.size())
		for f in failures:
			print("  " + f)
		quit(1)
