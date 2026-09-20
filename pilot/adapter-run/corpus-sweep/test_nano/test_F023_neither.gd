extends GdUnitTestSuite

func test_F023_neither() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_that(s.run(false, true)).is_equal("neither")
