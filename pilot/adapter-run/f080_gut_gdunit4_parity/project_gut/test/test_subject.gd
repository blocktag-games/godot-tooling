extends GutTest

const Subject = preload("res://subject/subject.gd")


func test_run_and_record_trace() -> void:
	var log: Array = []
	var r1 = Subject.run(3, log)
	var r2 = Subject.run(-1, log)
	assert_eq(r1, 6)
	assert_eq(r2, 0)

	var trace: Dictionary = {"log": log, "results": [r1, r2]}
	var f := FileAccess.open("user://trace.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(trace, "  "))
	f.close()
