extends GdUnitTestSuite
## Size read from PERF_W03_N, falling back to the FROZEN default --
## see tests_gut/test_workloads.gd's module comment for the (third,
## corrected) 2026-09-20 calibration and behavior-check fixes.

const DEFAULT_W03_N := 15667413


static func _write_work_time(workload: String, elapsed_usec: int) -> void:
	var f := FileAccess.open("res://work_time_%s.txt" % workload, FileAccess.WRITE)
	f.store_string(str(elapsed_usec))
	f.close()


static func _read_expected_json(workload: String) -> String:
	# Written to a file, not an env var: a large-n W11 probe's expected
	# JSON can reach ~270KB, over Linux's MAX_ARG_STRLEN (128KB) --
	# confirmed directly during recalibration.
	var path := "res://expected_%s.json" % workload
	if not FileAccess.file_exists(path):
		return ""
	var f := FileAccess.open(path, FileAccess.READ)
	var content := f.get_as_text()
	f.close()
	return content


func test_w03() -> void:
	var n_str := OS.get_environment("PERF_W03_N")
	var n := int(n_str) if not n_str.is_empty() else DEFAULT_W03_N
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")

	var start_usec := Time.get_ticks_usec()
	var result: Dictionary = subject.run(n)
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w03", elapsed_usec)

	var expected_json := _read_expected_json("w03")
	if not expected_json.is_empty():
		var expected: Dictionary = JSON.parse_string(expected_json)
		for key in ["low", "mid_low", "mid_high", "high", "very_high"]:
			assert_int(result.get(key, -1)).is_equal(int(expected[key]))
	else:
		assert_int(result.size()).is_equal(5)
