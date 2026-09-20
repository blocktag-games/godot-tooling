extends GdUnitTestSuite

func test_F011_default() -> void:
	var s = load("res://cases/f011_blank_comments_annotations/subject.gd")
	assert_that(s.run(3)).is_equal(6)
