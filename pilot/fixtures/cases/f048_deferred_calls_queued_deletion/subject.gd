extends Node

var log: Array[String] = []

func deferred_method() -> void:
	log.append("deferred_method_ran")

func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE:
		log.append("predelete")
