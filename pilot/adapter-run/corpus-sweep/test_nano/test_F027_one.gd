extends GdUnitTestSuite

func test_F027_one() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_that(s.run(1)).is_equal("one")
