extends RefCounted

signal resume_now

var log: Array[String] = []


func run() -> void:
	log.append("before_await")
	await resume_now
	log.append("after_resume")
