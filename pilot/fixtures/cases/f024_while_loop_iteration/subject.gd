extends RefCounted

static func run(n: int) -> int:
	var total: int = 0
	var i: int = 0
	while i < n:
		total += i
		i += 1
	return total
