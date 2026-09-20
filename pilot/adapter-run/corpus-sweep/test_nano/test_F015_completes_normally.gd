extends GdUnitTestSuite

func test_F015_completes_normally() -> void:
	var s = load("res://cases/f015_runtime_error_in_expression/subject.gd")
	assert_that(s.run(4)).is_equal(25)
