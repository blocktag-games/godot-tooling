extends GutTest

func test_run_passes() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 1)

func test_run_fails_deliberately() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 999)
