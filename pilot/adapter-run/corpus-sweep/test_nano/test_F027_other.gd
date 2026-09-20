extends GdUnitTestSuite

func test_F027_other() -> void:
	var s = load("res://cases/f027_match_fallback/subject.gd")
	assert_that(s.run(99)).is_equal("other")
