extends GdUnitTestSuite

func test_F022_none() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_that(s.run(-5)).is_equal("none")
