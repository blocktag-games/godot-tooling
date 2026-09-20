extends RefCounted

static func run(value: int) -> String:
	match value:
		1:
			return "one"
		2:
			return "two"
		_:
			return "other"
