extends RefCounted

signal resume_now

var log: Array[String] = []


func run() -> Array[String]:
	log.append("before_await")
	call_deferred("emit_signal", "resume_now")
	await resume_now
	log.append("after_resume")
	return log
