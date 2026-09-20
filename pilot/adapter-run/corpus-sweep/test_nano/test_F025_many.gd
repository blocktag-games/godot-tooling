extends GdUnitTestSuite

func test_F025_many() -> void:
	var s = load("res://cases/f025_for_loop_iteration/subject.gd")
	assert_that(s.run([1, 2, 3])).is_equal(6)
