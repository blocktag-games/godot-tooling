extends RefCounted

signal direct_signal
signal deferred_signal

var log: Array[String] = []

func _on_direct() -> void:
	log.append("direct_received")

func _on_deferred() -> void:
	log.append("deferred_received")

func run_direct() -> void:
	direct_signal.connect(_on_direct)
	log.append("before_direct_emit")
	direct_signal.emit()
	log.append("after_direct_emit")

func run_deferred() -> void:
	deferred_signal.connect(_on_deferred, CONNECT_DEFERRED)
	log.append("before_deferred_emit")
	deferred_signal.emit()
	log.append("after_deferred_emit")
