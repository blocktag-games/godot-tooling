extends GdUnitTestSuite

func test_F020_value_gt_0() -> void:
	var s = load("res://cases/f020_if_both_outcomes/subject.gd")
	assert_that(s.run(2)).is_equal(1)
