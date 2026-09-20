extends RefCounted

const Preloaded = preload("res://cases/f049_load_vs_preload/dependency.gd")

static func run(use_load: bool) -> int:
	if use_load:
		var loaded = load("res://cases/f049_load_vs_preload/dependency.gd")
		return loaded.value()
	return Preloaded.value()
