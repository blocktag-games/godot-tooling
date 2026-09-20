extends GdUnitTestSuite

func test_F002_default() -> void:
	var s = load("res://cases/f002_never_called/subject.gd")
	assert_that(s.called()).is_equal(1)
