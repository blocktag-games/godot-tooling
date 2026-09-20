extends GdUnitTestSuite
## PLACEHOLDER SIZE: not calibrated -- see tests_gut/test_workloads.gd's
## module comment.

const W03_N := 100000

func test_w03() -> void:
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")
	var result: Dictionary = subject.run(W03_N)
	assert_int(result.size()).is_equal(5)
