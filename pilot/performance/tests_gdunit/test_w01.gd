extends GdUnitTestSuite

func test_w01() -> void:
	var subject = load("res://workloads/w01_empty_app/subject.gd")
	assert_int(subject.run()).is_equal(42)
