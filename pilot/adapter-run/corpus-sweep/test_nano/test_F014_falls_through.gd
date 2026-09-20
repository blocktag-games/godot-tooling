extends GdUnitTestSuite

func test_F014_falls_through() -> void:
	var s = load("res://cases/f014_early_return/subject.gd")
	assert_that(s.run(false)).is_equal("late")
