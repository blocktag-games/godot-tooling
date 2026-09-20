extends RefCounted

static func make_adder(base: int) -> Callable:
	var add := func(y: int) -> int:
		return y + base
	return add

static func run(x: int, invoke: bool) -> int:
	var c: Callable = make_adder(x)
	if invoke:
		return c.call(10)
	return -1
