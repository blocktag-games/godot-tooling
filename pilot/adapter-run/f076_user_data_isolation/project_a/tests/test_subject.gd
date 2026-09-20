extends GutTest

func test_writes_own_sentinel() -> void:
	var f = FileAccess.open("user://sentinel_a.txt", FileAccess.WRITE)
	f.store_string("sentinel_from_project_a")
	f.close()
	var subject = load("res://subject/subject.gd")
	assert_eq(subject.run(), 1)
