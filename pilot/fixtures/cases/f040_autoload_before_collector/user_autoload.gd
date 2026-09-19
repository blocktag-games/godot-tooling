extends Node
## Stand-in for application code that runs at startup, e.g. game state
## initialized by a project autoload.

const EventLog = preload("res://event_log.gd")


func _ready() -> void:
	EventLog.record("user_ready:collector_active=%s" % EventLog.collector_active)
