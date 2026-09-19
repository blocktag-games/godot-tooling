extends GutTest

const Subject = preload("res://subject/subject.gd")


func test_true_branch() -> void:
	assert_eq(Subject.run(2), 1)


func test_false_branch() -> void:
	assert_eq(Subject.run(-2), -1)
