extends GdUnitTestSuite

func test_F049_uses_preloaded() -> void:
	var s = load("res://cases/f049_load_vs_preload/subject.gd")
	assert_that(s.run(false)).is_equal(99)
