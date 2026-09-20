extends GutTest

func test_slow_run() -> void:
	# Artificially slow, to give an outer harness timeout a real window
	# to fire while the Godot child process is still genuinely running.
	OS.delay_msec(15000)
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 1)
