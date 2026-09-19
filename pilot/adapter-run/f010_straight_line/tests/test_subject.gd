extends GutTest

const Subject = preload("res://subject/subject.gd")


func test_run_returns_seven_for_three() -> void:
	assert_eq(Subject.run(3), 7)
