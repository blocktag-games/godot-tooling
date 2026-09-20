extends RefCounted

static func run(value: int) -> String:
	var label: String = "positive" if value > 0 else "non_positive"
	return label
