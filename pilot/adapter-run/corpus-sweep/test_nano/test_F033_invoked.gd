extends GdUnitTestSuite

func test_F033_invoked() -> void:
	var s = load("res://cases/f033_lambda_and_callable/subject.gd")
	assert_that(s.run(5, true)).is_equal(15)
