extends RefCounted

class Base:
	func greet() -> String:
		return "base"

class Derived:
	extends Base
	func greet() -> String:
		return "derived:" + super.greet()

static func run(use_derived: bool) -> String:
	if use_derived:
		var d := Derived.new()
		return d.greet()
	var b := Base.new()
	return b.greet()
