extends GutTest

func test_slow_run() -> void:
	OS.delay_msec(15000)
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 1)
