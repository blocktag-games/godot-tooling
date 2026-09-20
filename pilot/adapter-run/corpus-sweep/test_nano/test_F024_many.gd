extends GdUnitTestSuite

func test_F024_many() -> void:
	var s = load("res://cases/f024_while_loop_iteration/subject.gd")
	assert_that(s.run(3)).is_equal(3)
