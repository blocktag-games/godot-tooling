extends GdUnitTestSuite
## Sizes read from PERF_W05_* env vars, falling back to FROZEN defaults
## -- see tests_gut/test_workloads.gd's module comment for the (third,
## corrected) 2026-09-20 calibration, including a real engine limit
## (5,000,000 queued deferred calls crashes Godot) discovered while
## calibrating this workload.

const DEFAULT_W05_N_LISTENERS := 50
const DEFAULT_W05_N_DIRECT := 140701
const DEFAULT_W05_N_DEFERRED := 140701


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


static func _write_work_time(workload: String, elapsed_usec: int) -> void:
	var f := FileAccess.open("res://work_time_%s.txt" % workload, FileAccess.WRITE)
	f.store_string(str(elapsed_usec))
	f.close()


func test_w05() -> void:
	var n_listeners := _env_int("PERF_W05_N_LISTENERS", DEFAULT_W05_N_LISTENERS)
	var n_direct := _env_int("PERF_W05_N_DIRECT", DEFAULT_W05_N_DIRECT)
	var n_deferred := _env_int("PERF_W05_N_DEFERRED", DEFAULT_W05_N_DEFERRED)
	var subject = load("res://workloads/w05_signals/subject.gd").new()

	var start_usec := Time.get_ticks_usec()
	subject.setup(n_listeners)
	subject.emit_direct(n_direct)
	subject.emit_deferred(n_deferred)
	await get_tree().process_frame
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w05", elapsed_usec)

	assert_int(subject.total_delivered()).is_equal(n_listeners * (n_direct + n_deferred))
