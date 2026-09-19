extends RefCounted

static func run(items: Array) -> int:
	var total: int = 0
	for item in items:
		total += item
	return total
