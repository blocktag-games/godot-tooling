extends SceneTree
## F048: deferred calls and queued deletion. call_deferred() and
## queue_free() both queue work that drains at the end of the current
## frame -- neither runs synchronously at the call site. This fixture's
## two inputs are two fresh processes, not two snapshots of one process
## (same rule as F041/F044): one awaits a frame before quitting, the
## other calls quit() immediately from _initialize().
##
## Corrected 2026-09-19 (second-reviewer pass): quit() only REQUESTS
## exit. Godot still runs one full main-loop iteration (MessageQueue
## flush, delete-queue drain, _process) before honoring it, so in the
## no_drain run the pending work still runs -- after the "log=" print
## below, but before the process exits. The print at the quit() site
## therefore shows only that nothing ran synchronously at the call site;
## _finalize() prints the log again so what actually ran before exit is
## observable by this driver itself, not just by an instrumented copy.
##
## Usage:
##   godot --headless --path . --script driver.gd            (awaits one frame)
##   godot --headless --path . --script driver.gd -- no_drain (quits immediately)

const Subject = preload("res://subject.gd")

var log_ref: Array


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := args[0] if args.size() > 0 else "default"

	var node = Subject.new()
	root.add_child(node)
	# Hold a direct reference to the log array, not the node itself --
	# queue_free() actually frees the node during the drained frame, and
	# accessing a freed object afterward is a runtime error (confirmed
	# empirically).
	log_ref = node.log
	node.call_deferred("deferred_method")
	node.queue_free()

	if mode == "no_drain":
		print("log=%s" % [log_ref])
		quit(0)
		return

	await process_frame
	print("log=%s" % [log_ref])
	quit(0)


func _finalize() -> void:
	print("log_at_finalize=%s" % [log_ref])
