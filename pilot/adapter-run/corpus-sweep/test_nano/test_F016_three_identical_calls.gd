extends GdUnitTestSuite

func test_F016_three_identical_calls() -> void:
	var s = load("res://cases/f016_repeated_invocation/subject.gd")
	assert_that(s.run(1)).is_equal(2)
	assert_that(s.run(1)).is_equal(2)
	assert_that(s.run(1)).is_equal(2)
