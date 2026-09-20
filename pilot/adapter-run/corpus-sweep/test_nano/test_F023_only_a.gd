extends GdUnitTestSuite

func test_F023_only_a() -> void:
	var s = load("res://cases/f023_nested_decisions/subject.gd")
	assert_that(s.run(true, false)).is_equal("only_a")
