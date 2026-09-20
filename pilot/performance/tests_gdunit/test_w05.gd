extends GdUnitTestSuite
## Sizes read from PERF_W05_* env vars, falling back to FROZEN defaults
## -- see tests_gut/test_workloads.gd's module comment for the (second,
## corrected) 2026-09-20 calibration, including a real engine limit
## (5,000,000 queued deferred calls crashes Godot) discovered while
## calibrating this workload.

const DEFAULT_W05_N_LISTENERS := 50
const DEFAULT_W05_N_DIRECT := 47386
const DEFAULT_W05_N_DEFERRED := 47386


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


func test_w05() -> void:
	var n_listeners := _env_int("PERF_W05_N_LISTENERS", DEFAULT_W05_N_LISTENERS)
	var n_direct := _env_int("PERF_W05_N_DIRECT", DEFAULT_W05_N_DIRECT)
	var n_deferred := _env_int("PERF_W05_N_DEFERRED", DEFAULT_W05_N_DEFERRED)
	var subject = load("res://workloads/w05_signals/subject.gd").new()
	subject.setup(n_listeners)
	subject.emit_direct(n_direct)
	subject.emit_deferred(n_deferred)
	await get_tree().process_frame
	assert_int(subject.total_delivered()).is_equal(n_listeners * (n_direct + n_deferred))
