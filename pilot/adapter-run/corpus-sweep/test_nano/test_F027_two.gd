extends GdUnitTestSuite

func test_F027_two() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_that(s.run(2)).is_equal("two")
