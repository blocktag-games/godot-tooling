extends GdUnitTestSuite

func test_F034_base_dispatch() -> void:
	var s = load("res://cases/f034_inheritance_and_super/subject.gd")
	assert_that(s.run(false)).is_equal("base")
