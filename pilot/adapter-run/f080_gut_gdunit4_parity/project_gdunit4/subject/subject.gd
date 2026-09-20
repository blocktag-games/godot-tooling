extends RefCounted

static func run(x: int, log: Array) -> int:
	log.append("start:%d" % x)
	var result: int
	if x > 0:
		log.append("positive_branch")
		result = x * 2
	else:
		log.append("non_positive_branch")
		result = 0
	log.append("end:%d" % result)
	return result
