extends GutTest
## gd-tools/GUT test wrapper for the four primary workloads. Calling
## each workload's fixed-work function directly inside a GUT test
## function is already "after the first idle frame" for free -- the
## _GDTCoverage autoload's _ready() (where gd-tools' instrumentation
## happens, per BP06's F081) runs during the test session's own
## startup, strictly before any test function body executes. The
## standalone-driver call_deferred pattern (drivers/*.gd) exists for
## the raw-engine correctness check (verify_workloads.py) specifically
## because THAT script has no test-runner session ahead of it.
##
## PLACEHOLDER SIZES: not calibrated. BP07's pilot (unexecuted as of
## this writing) sets these by requiring ~1-5s of B0 work per
## docs/benchmarks/performance-protocol.md. Any timing collected
## against these placeholders is NOT calibration or pilot data.

const W03_N := 100000
const W05_N_LISTENERS := 50
const W05_N_DIRECT := 500
const W05_N_DEFERRED := 500
const W11_N_STEPS := 1000
const W11_SEED := 12345


func test_w01() -> void:
	var subject = load("res://workloads/w01_empty_app/subject.gd")
	assert_eq(subject.run(), 42)


func test_w03() -> void:
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")
	var result: Dictionary = subject.run(W03_N)
	assert_true(result.size() == 5)


func test_w05() -> void:
	var subject = load("res://workloads/w05_signals/subject.gd").new()
	subject.setup(W05_N_LISTENERS)
	subject.emit_direct(W05_N_DIRECT)
	subject.emit_deferred(W05_N_DEFERRED)
	await get_tree().process_frame
	assert_eq(subject.total_delivered(), W05_N_LISTENERS * (W05_N_DIRECT + W05_N_DEFERRED))


func test_w11() -> void:
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)
	await subject.run_scenario(W11_N_STEPS, W11_SEED)
	assert_true(subject.final_state().has("score"))
	remove_child(subject)
	subject.free()
