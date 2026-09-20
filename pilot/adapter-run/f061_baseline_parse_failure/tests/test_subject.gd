extends GutTest

func test_run() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 1)
