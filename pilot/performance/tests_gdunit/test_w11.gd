extends GdUnitTestSuite
## PLACEHOLDER SIZES: not calibrated -- see tests_gut/test_workloads.gd's
## module comment.

const W11_N_STEPS := 1000
const W11_SEED := 12345

func test_w11() -> void:
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)
	await subject.run_scenario(W11_N_STEPS, W11_SEED)
	assert_bool(subject.final_state().has("score")).is_true()
	remove_child(subject)
	subject.free()
