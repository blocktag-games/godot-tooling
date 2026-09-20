extends GdUnitTestSuite

func test_F025_one() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_that(s.run([10])).is_equal(10)
