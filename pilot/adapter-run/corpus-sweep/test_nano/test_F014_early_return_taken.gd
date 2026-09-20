extends GdUnitTestSuite

func test_F014_early_return_taken() -> void:
	var s = load("res://cases/f014_early_return/subject.gd")
	assert_that(s.run(true)).is_equal("early")
