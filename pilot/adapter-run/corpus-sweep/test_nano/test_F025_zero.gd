extends GdUnitTestSuite

func test_F025_zero() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_that(s.run([])).is_equal(0)
