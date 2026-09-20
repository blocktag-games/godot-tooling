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
## Sizes are read from environment variables, falling back to the
## FROZEN defaults below -- this lets calibrate.py probe different
## sizes without editing this file per probe.
##
## FROZEN 2026-09-20 (SECOND, corrected calibration run -- a first
## calibration/pilot pass was invalid and fully retracted: see
## candidates.py's module docstring for why, and pilot/performance/
## README.md's postmortem). This run's calibration itself required a
## fix too: the original search used PROPORTIONAL scaling
## (new_n = old_n * target/elapsed), which is the wrong model for an
## AFFINE relationship (elapsed = fixed_floor + slope*n) -- a ~3.4-3.6s
## fixed process/GUT startup floor dominates completely at small n, so
## proportional scaling against it "converges" after one iteration
## without the workload's own compute ever mattering. Fixed by fitting
## an explicit two-point linear model and solving directly for the n
## landing at the target elapsed time (calibrate.py's linear_calibrate
## and calibrate_w05). See calibration_result.json for the fitted
## floor/slope per workload and the confirmation-probe timings.
##
## W05's calibration also surfaced a real ENGINE LIMIT, not a
## measurement artifact: 5,000,000 queued deferred calls
## (call_deferred("emit_signal", ...) with no frame drain in between)
## crashed Godot outright ("Message queue out of memory" -> SIGSEGV).
## The frozen n_direct/n_deferred below is well under that ceiling.

const DEFAULT_W03_N := 5599301
const DEFAULT_W05_N_LISTENERS := 50
const DEFAULT_W05_N_DIRECT := 47386
const DEFAULT_W05_N_DEFERRED := 47386
const DEFAULT_W11_N_STEPS := 568222
const DEFAULT_W11_SEED := 12345


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


func test_w01() -> void:
	var subject = load("res://workloads/w01_empty_app/subject.gd")
	assert_eq(subject.run(), 42)


func test_w03() -> void:
	var n := _env_int("PERF_W03_N", DEFAULT_W03_N)
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")
	var result: Dictionary = subject.run(n)
	assert_true(result.size() == 5)


func test_w05() -> void:
	var n_listeners := _env_int("PERF_W05_N_LISTENERS", DEFAULT_W05_N_LISTENERS)
	var n_direct := _env_int("PERF_W05_N_DIRECT", DEFAULT_W05_N_DIRECT)
	var n_deferred := _env_int("PERF_W05_N_DEFERRED", DEFAULT_W05_N_DEFERRED)
	var subject = load("res://workloads/w05_signals/subject.gd").new()
	subject.setup(n_listeners)
	subject.emit_direct(n_direct)
	subject.emit_deferred(n_deferred)
	await get_tree().process_frame
	assert_eq(subject.total_delivered(), n_listeners * (n_direct + n_deferred))


func test_w11() -> void:
	var n_steps := _env_int("PERF_W11_N_STEPS", DEFAULT_W11_N_STEPS)
	var seed_value := _env_int("PERF_W11_SEED", DEFAULT_W11_SEED)
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)
	await subject.run_scenario(n_steps, seed_value)
	assert_true(subject.final_state().has("score"))
	remove_child(subject)
	subject.free()
