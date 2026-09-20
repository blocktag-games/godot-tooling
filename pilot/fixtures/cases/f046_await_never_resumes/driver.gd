extends SceneTree
## F046: await that never resumes. The negative twin of F045 -- resume_now
## is never emitted, so run()'s continuation after the await must never be
## marked reached. Calling run() without awaiting its result lets the
## coroutine run synchronously up to the suspension point and return
## control immediately, confirmed empirically to leave the process free
## to quit cleanly with the coroutine still suspended.

const Subject = preload("res://subject.gd")


func _initialize() -> void:
	var subject = Subject.new()
	subject.run()
	print("log=%s" % [subject.log])
	quit(0)
