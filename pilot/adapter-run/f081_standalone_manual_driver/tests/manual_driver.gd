extends SceneTree
## F081: standalone/manual driver. No GUT anywhere in this script --
## coverage activation and collection are performed by hand, replicating
## exactly what gd-tools' pre_run_hook.gd (set_active(true)) and
## post_run_hook.gd (get_hits() -> JSON) do for a GUT run, proving that
## neither is actually GUT-specific: both are thin glue over a
## runner-agnostic autoload (_GDTCoverage).
##
## Usage: GD_TOOLS_COVERAGE_PLAN=<path to plan.json> godot --headless
##   --path . --script manual_driver.gd -- <output_path>

const TRACKER_NAME = "_GDTCoverage"


func _initialize() -> void:
	# _GDTCoverage's own _ready() (where instrumentation actually
	# happens, via reload(true)) has not run yet at this point --
	# autoload _ready() fires on the first idle frame, same as any
	# other node's _ready(), confirmed empirically: calling directly
	# from _initialize() sees the ORIGINAL, uninstrumented source and
	# silently collects zero hits. call_deferred lets that first frame
	# turn before anything below runs.
	call_deferred("_after_autoloads_ready")


func _after_autoloads_ready() -> void:
	var tracker = root.get_node_or_null(TRACKER_NAME)
	if tracker == null:
		printerr("manual_driver: _GDTCoverage autoload not found")
		quit(1)
		return

	# Replicates pre_run_hook.gd's ENTIRE job -- this is the only
	# activation step gd-tools' GUT integration performs.
	tracker.set_active(true)

	# Load (not preload) so this happens at run time, after the
	# _GDTCoverage autoload's own _ready() has already instrumented the
	# file via reload(true) during the autoload initialization phase.
	var subject = load("res://subject/subject.gd")
	subject.run(3)
	subject.run(0)

	# Replicates post_run_hook.gd's ENTIRE job.
	var hits: Dictionary = tracker.get_hits()
	var files: Array = []
	for file_id in hits:
		var file_hits: Dictionary = hits[file_id]
		var hits_dict: Dictionary = {}
		for line_id in file_hits:
			hits_dict[str(line_id)] = file_hits[line_id]
		files.append({"file_id": int(file_id), "hits": hits_dict})
	var data: Dictionary = {
		"version": 1,
		"generated_at": Time.get_datetime_string_from_system(true, false) + "Z",
		"files": files,
	}

	var args := OS.get_cmdline_user_args()
	var output_path := args[0] if args.size() > 0 else "res://manual_coverage.json"
	var f := FileAccess.open(output_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(data, "  "))
	f.close()

	quit(0)
