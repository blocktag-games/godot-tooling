extends SceneTree
## F043: process and physics callbacks. Drives the loop by a FIXED number
## of physics steps (deterministic, since Godot's physics tick rate is
## fixed), not by frame/process count (nondeterministic real-time-based --
## confirmed empirically to vary run to run). Do not assume process_count
## equals physics_count: this fixture exists specifically to demonstrate
## they don't have to.

const Subject = preload("res://subject.gd")

var node
var target_physics_steps := 3


func _initialize() -> void:
	node = Subject.new()
	root.add_child(node)


func _process(_delta: float) -> bool:
	if node.physics_count >= target_physics_steps:
		print("physics_count=%d process_count_at_least_one=%s" % [
			node.physics_count, node.process_count >= 1
		])
		root.remove_child(node)
		node.free()
		return true
	return false
