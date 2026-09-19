extends Node
## Stand-in for a coverage collector's own autoload. Models the one
## concrete fact read from gd-tools 0.4.0's addons/gd-tools-coverage/
## coverage.gd: the collector is itself a project autoload and activates
## instrumentation from within its own _ready(), via reload(true) on
## other autoload scripts. Whatever runs in another autoload's _ready()
## BEFORE this node's _ready() finishes cannot be instrumented by that
## mechanism, no matter what the collector's own contract claims.
##
## This fixture does not run any real collector -- it only establishes,
## independent of any specific tool, the ground-truth ordering fact that
## a real adapter's autoload position must be checked against in BP04.

const EventLog = preload("res://event_log.gd")


func _ready() -> void:
	EventLog.record("collector_marker_ready")
	EventLog.collector_active = true
