extends GdUnitTestSuite

func test_F010_default() -> void:
	var s = load("res://cases/f010_straight_line/subject.gd")
	assert_that(s.run(3)).is_equal(7)
