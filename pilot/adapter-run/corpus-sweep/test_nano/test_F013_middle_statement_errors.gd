extends GdUnitTestSuite

func test_F013_middle_statement_errors() -> void:
	var s = load("res://cases/f013_multiple_statements_per_line/subject.gd")
	assert_that(s.run(0, [])).is_equal(0)
