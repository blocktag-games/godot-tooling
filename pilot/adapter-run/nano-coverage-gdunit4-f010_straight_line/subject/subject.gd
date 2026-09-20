extends RefCounted

static func run(x: int) -> int:
	var doubled: int = x * 2
	var result: int = doubled + 1
	return result
