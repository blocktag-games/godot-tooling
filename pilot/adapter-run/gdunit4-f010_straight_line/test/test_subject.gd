extends GdUnitTestSuite

const Subject = preload("res://subject/subject.gd")


func test_run_returns_seven_for_three() -> void:
	assert_int(Subject.run(3)).is_equal(7)
