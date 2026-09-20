extends GutTest

func test_run_completes_normally() -> void:
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(4), 25)
