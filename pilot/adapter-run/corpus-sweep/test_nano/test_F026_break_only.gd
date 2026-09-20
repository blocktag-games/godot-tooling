extends GdUnitTestSuite

func test_F026_break_only() -> void:
	var s = load("res://cases/f026_break_continue/subject.gd")
	assert_that(s.run([200])).is_equal([])
