extends RefCounted

static func helper(x: int) -> int:
	return x * 2

static func run(x: int) -> int:
	return helper(x) + 1
