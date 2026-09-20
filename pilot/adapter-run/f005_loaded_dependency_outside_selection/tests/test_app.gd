extends GutTest

const App = preload("res://subject/app.gd")


func test_run_calls_excluded_dependency() -> void:
	assert_eq(App.run(), 11)
