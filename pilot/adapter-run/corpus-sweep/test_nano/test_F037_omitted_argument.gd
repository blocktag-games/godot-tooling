extends GdUnitTestSuite

func test_F037_omitted_argument() -> void:
	var s = load("res://cases/f037_default_arguments/subject.gd")
	assert_that(s.run(4)).is_equal(12)
