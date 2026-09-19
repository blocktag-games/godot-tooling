extends RefCounted
## Shared event log for the autoload-ordering fixtures. Not an autoload
## itself -- referenced via preload so it works with no project-wide
## global class cache (this project is never opened in the editor).

static var events: Array[String] = []
static var collector_active: bool = false


static func record(entry: String) -> void:
	events.append(entry)
