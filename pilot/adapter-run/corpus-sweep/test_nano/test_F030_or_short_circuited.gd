extends GdUnitTestSuite

func test_F030_or_short_circuited() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_that(s.run_or(true, false, log)).is_equal(true)
