extends SceneTree
## F044: direct vs. deferred signal delivery. A direct connection's
## callback fires synchronously inside emit(); a CONNECT_DEFERRED
## connection's callback is queued and only fires once the frame turns
## (confirmed empirically: never synchronously, always after an awaited
## process_frame). Order is carried by a log side-channel, same
## technique as F013/F030/F042.
##
## Usage:
##   godot --headless --path . --script driver.gd            (default: full run, frame turns)
##   godot --headless --path . --script driver.gd -- no_flush (quits before any frame turns)

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := args[0] if args.size() > 0 else "default"

	var direct_subject = Subject.new()
	direct_subject.run_direct()
	print("direct_log=%s" % [direct_subject.log])

	var deferred_subject = Subject.new()
	deferred_subject.run_deferred()
	print("deferred_log_before_frame=%s" % [deferred_subject.log])

	if mode == "no_flush":
		# Quit immediately. NOTE (corrected 2026-09-19): quit() only
		# requests exit -- Godot still runs one main-loop iteration
		# (including a MessageQueue flush) before honoring it. The
		# deferred callback never fires here because deferred_subject is
		# a RefCounted local that is freed when _initialize() returns,
		# before that flush, so the queued delivery has no live target
		# (verified: holding it in a member variable makes it fire).
		# Its own process, since a single cumulative report can't show
		# "never fired" if anything later in the SAME process delivered it.
		quit(0)
		return

	await process_frame
	print("deferred_log_after_frame=%s" % [deferred_subject.log])
	quit(0)
