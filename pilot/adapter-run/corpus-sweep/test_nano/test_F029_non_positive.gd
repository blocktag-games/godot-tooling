extends GdUnitTestSuite

func test_F029_non_positive() -> void:
	var s = load("res://cases/f029_conditional_expression/subject.gd")
	assert_that(s.run(-5)).is_equal("non_positive")
