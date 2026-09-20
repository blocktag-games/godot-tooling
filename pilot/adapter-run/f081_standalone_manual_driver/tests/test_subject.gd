extends GutTest

func test_positive() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(3), 6)

func test_zero() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(0), 0)
