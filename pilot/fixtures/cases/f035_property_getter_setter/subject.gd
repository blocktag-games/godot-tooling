extends RefCounted

var _value: int = 0
var value: int:
	get:
		return _value
	set(v):
		_value = v * 2

static func run(input: int) -> int:
	var obj = load("res://cases/f035_property_getter_setter/subject.gd").new()
	obj.value = input
	return obj.value
