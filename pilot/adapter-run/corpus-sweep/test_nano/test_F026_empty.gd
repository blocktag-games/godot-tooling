extends GdUnitTestSuite

func test_F026_empty() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_that(s.run([])).is_equal([])
