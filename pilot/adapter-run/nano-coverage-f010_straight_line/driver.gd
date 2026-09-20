extends SceneTree

const Subject = preload("res://subject/subject.gd")


func _initialize() -> void:
	if not Engine.has_singleton("NanoCoverage") and not ClassDB.class_exists("CoverageApi"):
		print("NANO_COVERAGE_NOT_LOADED")
		quit(1)
		return

	var bootstrapper = ProjectBootstrapper.new()
	bootstrapper.instrument_all_scripts()
	print("instrumented")

	var result = Subject.run(3)
	print("result=%d" % result)

	if Engine.has_singleton("NanoCoverage"):
		var nc = Engine.get_singleton("NanoCoverage")
		nc.save_session("f010_run")
		nc.reset()
		print("session saved")
	else:
		print("NO_NANOCOVERAGE_SINGLETON")
		quit(1)
		return

	var api = CoverageApi.new()
	var report_opts = {"workspace_id": "f010_run"}
	var report_result = api.generate_coverage_report(report_opts)
	print("report_result=%s" % [report_result])
	quit(0)
