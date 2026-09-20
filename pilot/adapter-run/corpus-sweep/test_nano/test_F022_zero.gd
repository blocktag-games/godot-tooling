extends GdUnitTestSuite

func test_F022_zero() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_that(s.run(0)).is_equal("zero")
