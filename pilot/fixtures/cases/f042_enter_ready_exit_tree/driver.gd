extends SceneTree
## F042: enter-tree, ready, and exit-tree callback ordering, using a log
## side-channel (same technique as F013/F030) so order is independently
## observable, not just whether each callback ran.

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var node = Subject.new()
	root.add_child(node)
	await process_frame
	root.remove_child(node)
	print("log=%s" % [node.log])
	node.free()
	quit(0)
