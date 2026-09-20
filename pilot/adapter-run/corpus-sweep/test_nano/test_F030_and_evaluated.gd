extends GdUnitTestSuite

func test_F030_and_evaluated() -> void:
	var s = load("res://cases/f030_short_circuit/subject.gd")
	var log: Array = []
	assert_that(s.run_and(true, true, log)).is_equal(true)
