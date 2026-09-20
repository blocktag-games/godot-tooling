extends RefCounted
## W05: Signals and deferred dispatch. A fixed number of listener
## objects connect to a shared signal; a fixed number of DIRECT
## emissions (delivered synchronously) and a fixed number of DEFERRED
## emissions (queued, delivered only once the frame drains -- BP06's
## F044 confirmed direct and deferred delivery differ materially) are
## performed. The driver keeps this object alive and reads final state
## AFTER an explicit drain, the same rule F044/F048 established: a
## coverage report (and this workload's own delivery count) is only
## meaningful once pending queued work has actually run.

signal pulse

var listeners: Array = []


func setup(n_listeners: int) -> void:
	for i in range(n_listeners):
		var counter := {"count": 0}
		listeners.append(counter)
		pulse.connect(func() -> void: counter["count"] += 1)


func emit_direct(n: int) -> void:
	for i in range(n):
		pulse.emit()


func emit_deferred(n: int) -> void:
	for i in range(n):
		call_deferred("emit_signal", "pulse")


func total_delivered() -> int:
	var total := 0
	for l in listeners:
		total += l["count"]
	return total
