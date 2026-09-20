extends GdUnitTestSuite

func test_F036_default() -> void:
	var s = load("res://cases/f036_typed_collections_signatures/subject.gd")
	var items: Array[int] = [1, 2, 3]
	assert_that(s.run(items)).is_equal({1: 1, 2: 4, 3: 9})
