extends GdUnitTestSuite

func test_F015_reached_but_not_completed() -> void:
	var s = load("res://cases/f015_runtime_error_in_expression/subject.gd")
	assert_that(s.run(0)).is_equal(0)
