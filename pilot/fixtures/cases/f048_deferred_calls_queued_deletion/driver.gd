extends SceneTree
## F048: deferred calls and queued deletion. call_deferred() and
## queue_free() both queue work that drains at the end of the current
## frame -- neither runs synchronously at the call site. This fixture's
## two inputs are two fresh processes, not two snapshots of one process
## (same rule as F041/F044): one drains a frame before quitting, the
## other quits immediately, so the pending work's fate ("included or
## excluded" per the catalog requirement) is a real, mechanically
## distinct fact in each process's own coverage report.
##
## Usage:
##   godot --headless --path . --script driver.gd            (drains one frame)
##   godot --headless --path . --script driver.gd -- no_drain (quits immediately)

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := args[0] if args.size() > 0 else "default"

	var node = Subject.new()
	root.add_child(node)
	# Hold a direct reference to the log array, not the node itself --
	# queue_free() actually frees the node during the drained frame, and
	# accessing a freed object afterward is a runtime error (confirmed
	# empirically).
	var log_ref: Array = node.log
	node.call_deferred("deferred_method")
	node.queue_free()

	if mode == "no_drain":
		print("log=%s" % [log_ref])
		quit(0)
		return

	await process_frame
	print("log=%s" % [log_ref])
	quit(0)
