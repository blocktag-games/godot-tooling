extends GdUnitTestSuite

func test_F012_default() -> void:
	var s = load("res://cases/f012_multiline_expression/subject.gd")
	assert_that(s.run(1, 2, 3)).is_equal(6)
