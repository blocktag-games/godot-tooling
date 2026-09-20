extends RefCounted

static var static_init_count: int = 0
var instance_init_count: int = 0

static func _static_init() -> void:
	static_init_count += 1

func _init() -> void:
	instance_init_count += 1

static func run(num_instances: int) -> Dictionary:
	var instances: Array = []
	for i in range(num_instances):
		instances.append(new())
	return {"static_init_count": static_init_count, "num_instances_created": instances.size()}
