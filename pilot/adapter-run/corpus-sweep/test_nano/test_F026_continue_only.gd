extends GdUnitTestSuite

func test_F026_continue_only() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_that(s.run([-1, 5])).is_equal([5])
