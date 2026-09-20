extends RefCounted

static func run(items: Array[int]) -> Dictionary:
	var result: Dictionary = {}
	for item in items:
		result[item] = item * item
	return result
