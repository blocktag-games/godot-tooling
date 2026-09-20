extends GdUnitTestSuite
## Sizes read from PERF_W11_* env vars, falling back to FROZEN defaults
## -- see tests_gut/test_workloads.gd's module comment for the (second,
## corrected) 2026-09-20 calibration.

const DEFAULT_W11_N_STEPS := 568222
const DEFAULT_W11_SEED := 12345


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


func test_w11() -> void:
	var n_steps := _env_int("PERF_W11_N_STEPS", DEFAULT_W11_N_STEPS)
	var seed_value := _env_int("PERF_W11_SEED", DEFAULT_W11_SEED)
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)
	await subject.run_scenario(n_steps, seed_value)
	assert_bool(subject.final_state().has("score")).is_true()
	remove_child(subject)
	subject.free()
