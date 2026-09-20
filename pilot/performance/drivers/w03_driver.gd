extends SceneTree
## W03 driver. See w01_driver.gd for why work starts after the first
## idle frame.
##
## Usage: godot --headless --path . --script drivers/w03_driver.gd -- <n>

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var n := int(args[0]) if args.size() > 0 else 1000
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")
	var result: Dictionary = subject.run(n)
	print(JSON.stringify(result))
	quit(0)
