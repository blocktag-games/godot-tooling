extends RefCounted

static func run(value: int) -> int:
	var outcome: int
	if value > 0:
		outcome = 1
	else:
		outcome = -1
	return outcome
