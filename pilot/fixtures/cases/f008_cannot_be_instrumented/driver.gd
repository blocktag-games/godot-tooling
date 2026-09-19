extends SceneTree
## Uninstrumented ground truth: proves unparseable.gd's UTF-8 BOM prefix
## is accepted and run correctly by the Godot 4.7.1 engine itself, so
## any inability to instrument it later is specific to a collector's own
## tooling (e.g. a second parser), not to the file being genuinely
## invalid GDScript.

const Unparseable = preload("res://unparseable.gd")
const Normal = preload("res://normal.gd")


func _initialize() -> void:
	print("unparseable_result=%d" % Unparseable.run())
	print("normal_result=%d" % Normal.run())
	quit(0)
