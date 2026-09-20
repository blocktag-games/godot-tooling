extends Node

var process_count: int = 0
var physics_count: int = 0

func _process(_delta: float) -> void:
	process_count += 1

func _physics_process(_delta: float) -> void:
	physics_count += 1
