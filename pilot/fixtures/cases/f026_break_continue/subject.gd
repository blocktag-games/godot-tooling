extends RefCounted

static func run(items: Array) -> Array:
	var result: Array = []
	for item in items:
		if item < 0:
			continue
		if item > 100:
			break
		result.append(item)
	return result
