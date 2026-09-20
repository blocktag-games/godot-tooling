extends SceneTree
## Standalone probe: calls subject.gd:run(0) (a deliberate runtime
## division-by-zero) and lets the engine's own SCRIPT ERROR diagnostic
## report the line. Run twice by check.py -- once with no
## GD_TOOLS_COVERAGE_PLAN set (uninstrumented, reports the TRUE source
## line) and once with it set to a real plan.json from an actual
## `gd-tools test --coverage` run on this same fixture (instrumented,
## reports whatever line gd-tools' tracker insertion shifted the error
## to). Deferred past the first idle frame so the _GDTCoverage
## autoload's own _ready() (where Script.reload(true) instrumentation
## actually happens) has already run before this calls into the
## subject -- same timing fact established while building F081.

func _initialize() -> void:
	call_deferred("_after_autoloads_ready")


func _after_autoloads_ready() -> void:
	var subject = load("res://subject/subject.gd")
	subject.run(0)
	quit(0)
