extends SceneTree

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var subject = Subject.new()
	var result: Array = await subject.run()
	print("log=%s" % [result])
	quit(0)
