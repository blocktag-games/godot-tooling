extends GdUnitTestSuite

func test_F001_default() -> void:
	var s = load("res://cases/f001_never_loaded/loaded.gd")
	assert_that(s.run()).is_equal(42)
