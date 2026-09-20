extends GutTest
## BP06 corpus sweep: one test function per (fixture, oracle input) pair,
## reproducing the exact call the oracle documents. Each is run in
## isolation via `gd-tools test --coverage --test <func_name>`, one
## real gd-tools invocation per input, never batched -- a shared
## process's coverage report is cumulative and would falsely satisfy
## every "not yet reached" obligation from an input run earlier in the
## same process.

func test_F001_default() -> void:
	var s = load("res://cases/f001_never_loaded/loaded.gd")
	assert_eq(s.run(), 42)

func test_F002_default() -> void:
	var s = load("res://cases/f002_never_called/subject.gd")
	assert_eq(s.called(), 1)

func test_F010_default() -> void:
	var s = load("res://cases/f010_straight_line/subject.gd")
	assert_eq(s.run(3), 7)

func test_F012_default() -> void:
	var s = load("res://cases/f012_multiline_expression/subject.gd")
	assert_eq(s.run(1, 2, 3), 6)

func test_F020_value_gt_0() -> void:
	var s = load("res://cases/f020_if_both_outcomes/subject.gd")
	assert_eq(s.run(2), 1)

func test_F020_value_lte_0() -> void:
	var s = load("res://cases/f020_if_both_outcomes/subject.gd")
	assert_eq(s.run(-2), -1)

func test_F021_value_gt_0() -> void:
	var s = load("res://cases/f021_if_without_else/subject.gd")
	assert_eq(s.run(5), 5)

func test_F021_value_lte_0() -> void:
	var s = load("res://cases/f021_if_without_else/subject.gd")
	assert_eq(s.run(-5), 0)

func test_F022_big() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_eq(s.run(15), "big")

func test_F022_small() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_eq(s.run(5), "small")

func test_F022_zero() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_eq(s.run(0), "zero")

func test_F022_none() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_eq(s.run(-5), "none")

func test_F023_both() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_eq(s.run(true, true), "both")

func test_F023_only_a() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_eq(s.run(true, false), "only_a")

func test_F023_neither() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_eq(s.run(false, true), "neither")

func test_F024_zero() -> void:
	var s = load("res://cases/f024_while_loop_iteration/subject.gd")
	assert_eq(s.run(0), 0)

func test_F024_one() -> void:
	var s = load("res://cases/f024_while_loop_iteration/subject.gd")
	assert_eq(s.run(1), 0)

func test_F024_many() -> void:
	var s = load("res://cases/f024_while_loop_iteration/subject.gd")
	assert_eq(s.run(3), 3)

func test_F025_zero() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_eq(s.run([]), 0)

func test_F025_one() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_eq(s.run([10]), 10)

func test_F025_many() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_eq(s.run([1, 2, 3]), 6)

func test_F026_continue_only() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_eq(s.run([-1, 5]), [5])

func test_F026_break_only() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_eq(s.run([200]), [])

func test_F026_neither() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_eq(s.run([5]), [5])

func test_F026_empty() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_eq(s.run([]), [])

func test_F027_one() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_eq(s.run(1), "one")

func test_F027_two() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_eq(s.run(2), "two")

func test_F027_other() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_eq(s.run(99), "other")

func test_F029_positive() -> void:
	var s = load("res://cases/f029_conditional_expression/subject.gd")
	assert_eq(s.run(5), "positive")

func test_F029_non_positive() -> void:
	var s = load("res://cases/f029_conditional_expression/subject.gd")
	assert_eq(s.run(-5), "non_positive")

func test_F030_and_evaluated() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_eq(s.run_and(true, true, log), true)

func test_F030_and_short_circuited() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_eq(s.run_and(false, true, log), false)

func test_F030_or_evaluated() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_eq(s.run_or(false, true, log), true)

func test_F030_or_short_circuited() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_eq(s.run_or(true, false, log), true)

func test_F011_default() -> void:
	var s = load("res://cases/f011_blank_comments_annotations/subject.gd")
	assert_eq(s.run(3), 6)

func test_F013_all_complete() -> void:
	var s = load("res://cases/f013_multiple_statements_per_line/subject.gd")
	assert_eq(s.run(2, []), 50)

func test_F013_middle_statement_errors() -> void:
	var s = load("res://cases/f013_multiple_statements_per_line/subject.gd")
	assert_eq(s.run(0, []), 0)

func test_F014_early_return_taken() -> void:
	var s = load("res://cases/f014_early_return/subject.gd")
	assert_eq(s.run(true), "early")

func test_F014_falls_through() -> void:
	var s = load("res://cases/f014_early_return/subject.gd")
	assert_eq(s.run(false), "late")

func test_F015_completes_normally() -> void:
	var s = load("res://cases/f015_runtime_error_in_expression/subject.gd")
	assert_eq(s.run(4), 25)

func test_F015_reached_but_not_completed() -> void:
	var s = load("res://cases/f015_runtime_error_in_expression/subject.gd")
	assert_eq(s.run(0), 0)

func test_F016_three_identical_calls() -> void:
	var s = load("res://cases/f016_repeated_invocation/subject.gd")
	assert_eq(s.run(1), 2)
	assert_eq(s.run(1), 2)
	assert_eq(s.run(1), 2)

func test_F032_default() -> void:
	var s = load("res://cases/f032_static_functions/subject.gd")
	assert_eq(s.run(3), 7)

func test_F033_invoked() -> void:
	var s = load("res://cases/f033_lambda_and_callable/subject.gd")
	assert_eq(s.run(5, true), 15)

func test_F033_made_but_not_invoked() -> void:
	var s = load("res://cases/f033_lambda_and_callable/subject.gd")
	assert_eq(s.run(5, false), -1)

func test_F034_derived_dispatch() -> void:
	var s = load("res://cases/f034_inheritance_and_super/subject.gd")
	assert_eq(s.run(true), "derived:base")

func test_F034_base_dispatch() -> void:
	var s = load("res://cases/f034_inheritance_and_super/subject.gd")
	assert_eq(s.run(false), "base")

func test_F035_default() -> void:
	var s = load("res://cases/f035_property_getter_setter/subject.gd")
	assert_eq(s.run(5), 10)

func test_F036_default() -> void:
	var s = load("res://cases/f036_typed_collections_signatures/subject.gd")
	var items: Array[int] = [1, 2, 3]
	assert_eq(s.run(items), {1: 1, 2: 4, 3: 9})

func test_F037_omitted_argument() -> void:
	var s = load("res://cases/f037_default_arguments/subject.gd")
	assert_eq(s.run(4), 12)

func test_F037_supplied_argument() -> void:
	var s = load("res://cases/f037_default_arguments/subject.gd")
	assert_eq(s.run(4, 10), 40)

func test_F049_uses_preloaded() -> void:
	var s = load("res://cases/f049_load_vs_preload/subject.gd")
	assert_eq(s.run(false), 99)

func test_F049_uses_loaded() -> void:
	var s = load("res://cases/f049_load_vs_preload/subject.gd")
	assert_eq(s.run(true), 99)
