extends GdUnitTestSuite

func test_F021_value_gt_0() -> void:
	var s = load("res://cases/f021_if_without_else/subject.gd")
	assert_that(s.run(5)).is_equal(5)
