extends GdUnitTestSuite
## Size read from PERF_W03_N, falling back to the FROZEN default --
## see tests_gut/test_workloads.gd's module comment for the (second,
## corrected) 2026-09-20 calibration.

const DEFAULT_W03_N := 5599301


func test_w03() -> void:
	var n_str := OS.get_environment("PERF_W03_N")
	var n := int(n_str) if not n_str.is_empty() else DEFAULT_W03_N
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")
	var result: Dictionary = subject.run(n)
	assert_int(result.size()).is_equal(5)
