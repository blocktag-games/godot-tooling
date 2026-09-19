extends Node
## Stand-in for a user autoload carrying mutable state, e.g. game state
## or a save-data manager, that already exists when a coverage collector
## instruments its script in place.

var counter: int = 0


func _ready() -> void:
	counter += 1
