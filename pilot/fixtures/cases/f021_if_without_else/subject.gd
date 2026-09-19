extends RefCounted

static func run(value: int) -> int:
	var outcome: int = 0
	if value > 0:
		outcome = value
	return outcome
