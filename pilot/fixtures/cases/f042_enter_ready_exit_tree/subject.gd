extends Node

var log: Array[String] = []

func _enter_tree() -> void:
	log.append("enter_tree")

func _ready() -> void:
	log.append("ready")

func _exit_tree() -> void:
	log.append("exit_tree")
