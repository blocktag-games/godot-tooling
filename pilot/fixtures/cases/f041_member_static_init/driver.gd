extends SceneTree
## F041: member and static initialization, run as its own mini-project so
## each named input is a genuinely fresh process (per the catalog's
## "Fresh-process initial state and init events" oracle basis) -- not two
## calls sharing one process's cumulative coverage report, which could
## never actually distinguish "ran once at load" from "ran once per call".
##
## Usage: godot --headless --path . --script driver.gd -- <num_instances>

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var num_instances := int(args[0]) if args.size() > 0 else 0
	var result: Dictionary = Subject.run(num_instances)
	print("num_instances=%d result=%s" % [num_instances, result])
	quit(0)
