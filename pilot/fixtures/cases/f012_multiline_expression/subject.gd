extends RefCounted

static func run(a: int, b: int, c: int) -> int:
	var total: int = (
		a
		+ b
		+ c
	)
	return total
