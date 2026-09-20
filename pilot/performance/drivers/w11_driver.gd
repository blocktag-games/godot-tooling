extends SceneTree
## W11 driver. See w01_driver.gd for why work starts after the first
## idle frame. run_scenario() itself awaits mid-scenario, so the driver
## must await its completion (not just call it) before reading final
## state.
##
## Usage: godot --headless --path . --script drivers/w11_driver.gd -- <n_steps> <seed>

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var n_steps := int(args[0]) if args.size() > 0 else 200
	var seed_value := int(args[1]) if args.size() > 1 else 12345

	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	root.add_child(subject)
	await subject.run_scenario(n_steps, seed_value)

	var result: Dictionary = subject.final_state()
	result["n_steps"] = n_steps
	result["seed"] = seed_value
	print(JSON.stringify(result))

	root.remove_child(subject)
	subject.free()
	quit(0)
