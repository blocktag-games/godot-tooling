extends RefCounted

static func run(value: int) -> String:
	var result: String = "none"
	if value > 10:
		result = "big"
	elif value > 0:
		result = "small"
	elif value == 0:
		result = "zero"
	return result
