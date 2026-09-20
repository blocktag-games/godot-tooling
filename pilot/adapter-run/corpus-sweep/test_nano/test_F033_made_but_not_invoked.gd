extends GdUnitTestSuite

func test_F033_made_but_not_invoked() -> void:
	var s = load("res://cases/f033_lambda_and_callable/subject.gd")
	assert_that(s.run(5, false)).is_equal(-1)
