extends GdUnitTestSuite
## PLACEHOLDER SIZES: not calibrated -- see tests_gut/test_workloads.gd's
## module comment.

const W05_N_LISTENERS := 50
const W05_N_DIRECT := 500
const W05_N_DEFERRED := 500

func test_w05() -> void:
	var subject = load("res://workloads/w05_signals/subject.gd").new()
	subject.setup(W05_N_LISTENERS)
	subject.emit_direct(W05_N_DIRECT)
	subject.emit_deferred(W05_N_DEFERRED)
	await get_tree().process_frame
	assert_int(subject.total_delivered()).is_equal(W05_N_LISTENERS * (W05_N_DIRECT + W05_N_DEFERRED))
