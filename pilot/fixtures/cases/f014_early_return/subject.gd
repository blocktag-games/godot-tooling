extends RefCounted

static func run(flag: bool) -> String:
	if flag:
		return "early"
	var later: String = "late"
	return later
