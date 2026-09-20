extends SceneTree
## W05 driver. See w01_driver.gd for why work starts after the first
## idle frame. Reads final state only AFTER an explicit drain -- the
## deferred emissions are queued, not delivered, until a frame turns
## (BP06's F044).
##
## Usage: godot --headless --path . --script drivers/w05_driver.gd -- <n_listeners> <n_direct> <n_deferred>

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var n_listeners := int(args[0]) if args.size() > 0 else 50
	var n_direct := int(args[1]) if args.size() > 1 else 500
	var n_deferred := int(args[2]) if args.size() > 2 else 500

	var subject = load("res://workloads/w05_signals/subject.gd").new()
	subject.setup(n_listeners)
	subject.emit_direct(n_direct)
	subject.emit_deferred(n_deferred)
	await process_frame  # drain the deferred queue before reading final state

	var result := {
		"n_listeners": n_listeners,
		"n_direct": n_direct,
		"n_deferred": n_deferred,
		"total_delivered": subject.total_delivered(),
		"expected_total": n_listeners * (n_direct + n_deferred),
	}
	print(JSON.stringify(result))
	quit(0)
