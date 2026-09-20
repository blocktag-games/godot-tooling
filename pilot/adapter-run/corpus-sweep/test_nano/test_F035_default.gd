extends GdUnitTestSuite

func test_F035_default() -> void:
	var s = load("res://cases/f035_property_getter_setter/subject.gd")
	assert_that(s.run(5)).is_equal(10)
