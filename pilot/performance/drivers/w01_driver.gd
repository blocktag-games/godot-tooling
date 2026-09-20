extends SceneTree
## W01 driver. Deferred past the first idle frame before doing anything,
## matching gd-tools' own instrumentation timing (BP06's F081 finding:
## its coverage autoload instruments in _ready(), which fires on the
## first idle frame, not synchronously) -- so B0 (uninstrumented) and C
## (instrumented) both start their measured work at the same logical
## point in the process lifecycle, not one starting earlier than the
## other by construction.

func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var subject = load("res://workloads/w01_empty_app/subject.gd")
	var result: int = subject.run()
	print(JSON.stringify({"sentinel_result": result}))
	quit(0)
