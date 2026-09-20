extends "res://addons/gut/hook_script.gd"

const Coverage = preload("res://addons/coverage/coverage.gd")


func run():
	var coverage = Coverage.instance
	coverage.save_coverage_file("res://coverage_output.json")
	coverage.finalize(Coverage.Verbosity.ALL_FILES)
