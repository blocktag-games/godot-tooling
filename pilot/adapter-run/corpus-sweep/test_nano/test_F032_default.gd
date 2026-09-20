extends GdUnitTestSuite

func test_F032_default() -> void:
	var s = load("res://cases/f032_static_functions/subject.gd")
	assert_that(s.run(3)).is_equal(7)
