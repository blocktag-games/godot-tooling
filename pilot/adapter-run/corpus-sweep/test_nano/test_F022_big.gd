extends GdUnitTestSuite

func test_F022_big() -> void:
	var s = load("res://cases/f022_elif_chain/subject.gd")
	assert_that(s.run(15)).is_equal("big")
