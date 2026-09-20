extends GdUnitTestSuite

func test_F013_all_complete() -> void:
	var s = load("res://cases/f013_multiple_statements_per_line/subject.gd")
	assert_that(s.run(2, [])).is_equal(50)
