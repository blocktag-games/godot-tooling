extends RefCounted

static func run(divisor: int, log: Array) -> int:
	log.append("first"); var result: int = 100 / divisor; log.append("second")
	return result
