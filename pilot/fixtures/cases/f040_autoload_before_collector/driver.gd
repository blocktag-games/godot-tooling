extends SceneTree
## Uninstrumented ground-truth driver: records the observed autoload
## _ready() order and prints it for comparison against this case's oracle.
##
## Autoload _ready() notifications are not delivered synchronously during
## _initialize() -- they are queued and flushed on the first processed
## frame. _process() is therefore where the recorded order is read.

const EventLog = preload("res://event_log.gd")


func _process(_delta: float) -> bool:
	for entry in EventLog.events:
		print(entry)
	return true
