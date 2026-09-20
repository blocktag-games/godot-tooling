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

	# F022: elif chain -- each arm, and the no-arm-matched case.
	var f022 = load("res://cases/f022_elif_chain/subject.gd")
	_check("F022", "run(15) first arm", f022.run(15), "big")
	_check("F022", "run(5) second arm", f022.run(5), "small")
	_check("F022", "run(0) third arm", f022.run(0), "zero")
	_check("F022", "run(-5) no arm matched", f022.run(-5), "none")

	# F023: nested decisions -- the inner if must not execute at all when
	# the outer condition excludes it, not merely evaluate false.
	var f023 = load("res://cases/f023_nested_decisions/subject.gd")
	_check("F023", "run(true, true) both", f023.run(true, true), "both")
	_check("F023", "run(true, false) only_a", f023.run(true, false), "only_a")
	_check("F023", "run(false, true) neither, inner never reached", f023.run(false, true), "neither")

	# F024: while loop with zero, one, and many iterations.
	var f024 = load("res://cases/f024_while_loop_iteration/subject.gd")
	_check("F024", "run(0) zero iterations", f024.run(0), 0)
	_check("F024", "run(1) one iteration", f024.run(1), 0)
	_check("F024", "run(3) many iterations", f024.run(3), 3)

	# F026: break and continue -- each isolated, plus a normal pass and
	# an empty input so the loop header's own zero-iteration case is
	# still covered here too.
	var f026 = load("res://cases/f026_break_continue/subject.gd")
	_check("F026", "run([-1, 5]) continue only", f026.run([-1, 5]), [5])
	_check("F026", "run([200]) break only", f026.run([200]), [])
	_check("F026", "run([5]) neither", f026.run([5]), [5])
	_check("F026", "run([]) empty, loop never entered", f026.run([]), [])

	# F027: match with two literal arms and a fallback.
	var f027 = load("res://cases/f027_match_fallback/subject.gd")
	_check("F027", "run(1) first arm", f027.run(1), "one")
	_check("F027", "run(2) second arm", f027.run(2), "two")
	_check("F027", "run(99) fallback", f027.run(99), "other")

	# F029: conditional expression (ternary) -- both arms live on one
	# physical line, so a whole-line hit alone can't distinguish them.
	var f029 = load("res://cases/f029_conditional_expression/subject.gd")
	_check("F029", "run(5) true arm", f029.run(5), "positive")
	_check("F029", "run(-5) false arm", f029.run(-5), "non_positive")

	# F030: short-circuit and/or. The return value alone cannot prove
	# short-circuiting happened (e.g. "false and X" returns false whether
	# or not X ran), so a log array records whether the right operand's
	# lambda body actually executed -- the real, observable ground truth.
	var f030 = load("res://cases/f030_short_circuit/subject.gd")
	var log_and_eval: Array = []
	_check("F030", "run_and(true, true) result", f030.run_and(true, true, log_and_eval), true)
	_check("F030", "run_and(true, true) right WAS evaluated", log_and_eval, ["right_evaluated"])

	var log_and_short: Array = []
	_check("F030", "run_and(false, true) result", f030.run_and(false, true, log_and_short), false)
	_check("F030", "run_and(false, true) right NOT evaluated", log_and_short, [])

	var log_or_eval: Array = []
	_check("F030", "run_or(false, true) result", f030.run_or(false, true, log_or_eval), true)
	_check("F030", "run_or(false, true) right WAS evaluated", log_or_eval, ["right_evaluated"])

	var log_or_short: Array = []
	_check("F030", "run_or(true, false) result", f030.run_or(true, false, log_or_short), true)
	_check("F030", "run_or(true, false) right NOT evaluated", log_or_short, [])

	# F011: blank lines, comments, and annotations are nonexecuting text --
	# only the var assignment and return are real obligations.
	var f011 = load("res://cases/f011_blank_comments_annotations/subject.gd")
	_check("F011", "run(3)", f011.run(3), 6)

	# F013: two statements on one physical line via a semicolon. A
	# runtime error mid-line lets the first statement complete while the
	# second (and the following line) never do, even though the line was
	# reached.
	var f013 = load("res://cases/f013_multiple_statements_per_line/subject.gd")
	_check("F013", "run(2) both statements complete", f013.run(2), 50)
	_check("F013", "run(0) second statement errors, first still ran", f013.run(0), 0)

	# F014: early return -- code textually after the taken return must
	# not be falsely marked hit for that call.
	var f014 = load("res://cases/f014_early_return/subject.gd")
	_check("F014", "run(true) early return taken", f014.run(true), "early")
	_check("F014", "run(false) falls through to later code", f014.run(false), "late")

	# F015: runtime error within an expression -- the line is reached
	# (evaluation starts) but never completes (assignment never happens,
	# the function aborts, and the following return is never reached).
	var f015 = load("res://cases/f015_runtime_error_in_expression/subject.gd")
	_check("F015", "run(4) completes normally", f015.run(4), 25)
	_check("F015", "run(0) reached but not completed, coerces to 0", f015.run(0), 0)

	# F016: repeated invocation -- the hit set stays stable across
	# multiple identical calls; this only asserts return-value stability,
	# not any specific count semantics (that's a per-tool question).
	var f016 = load("res://cases/f016_repeated_invocation/subject.gd")
	_check("F016", "run(1) call 1", f016.run(1), 2)
	_check("F016", "run(1) call 2", f016.run(1), 2)
	_check("F016", "run(1) call 3", f016.run(1), 2)

	print("")
	if failures.is_empty():
		print("All tier-0 group 1 fixtures match their behavioral specification.")
		quit(0)
	else:
		print("%d failure(s):" % failures.size())
		for f in failures:
			print("  " + f)
		quit(1)
