extends GdUnitTestSuite
## Sizes read from PERF_W11_* env vars, falling back to FROZEN defaults
## -- see tests_gut/test_workloads.gd's module comment for the (third,
## corrected) 2026-09-20 calibration.

const DEFAULT_W11_N_STEPS := 1671580
const DEFAULT_W11_SEED := 12345


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


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


func test_w11() -> void:
	var n_steps := _env_int("PERF_W11_N_STEPS", DEFAULT_W11_N_STEPS)
	var seed_value := _env_int("PERF_W11_SEED", DEFAULT_W11_SEED)
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)

	var start_usec := Time.get_ticks_usec()
	await subject.run_scenario(n_steps, seed_value)
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w11", elapsed_usec)

	var final: Dictionary = subject.final_state()
	var expected_json := _read_expected_json("w11")
	if not expected_json.is_empty():
		var expected: Dictionary = JSON.parse_string(expected_json)
		assert_int(final.get("score", -999999)).is_equal(int(expected["score"]))
		assert_int(final.get("health", -999999)).is_equal(int(expected["health"]))
		assert_int(final.get("log_length", -1)).is_equal(int(expected["log_length"]))
		var expected_milestones: Array = expected["milestones"]
		var actual_milestones: Array = final.get("milestones", [])
		assert_int(actual_milestones.size()).is_equal(expected_milestones.size())
		for i in range(min(actual_milestones.size(), expected_milestones.size())):
			assert_int(actual_milestones[i]).is_equal(int(expected_milestones[i]))
	else:
		assert_bool(final.has("score")).is_true()

	remove_child(subject)
	subject.free()
