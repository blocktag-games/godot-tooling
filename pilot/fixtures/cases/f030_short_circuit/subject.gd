extends RefCounted

static func run_and(left: bool, right: bool, log: Array) -> bool:
	var mark := func() -> bool:
		log.append("right_evaluated")
		return right
	return left and mark.call()


static func run_or(left: bool, right: bool, log: Array) -> bool:
	var mark := func() -> bool:
		log.append("right_evaluated")
		return right
	return left or mark.call()
