extends GdUnitTestSuite

func test_F023_both() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_that(s.run(true, true)).is_equal("both")
