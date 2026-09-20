extends RefCounted

static func run(a: bool, b: bool) -> String:
	if a:
		if b:
			return "both"
		return "only_a"
	return "neither"
