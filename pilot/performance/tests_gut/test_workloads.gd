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
## **Corrected 2026-09-20, a review of BP07/BP08/BP09's completed work
## against the catalog/protocol found two real defects here, both fixed
## in this pass:**
##
## 1. The frozen sizes below were calibrated against TOTAL PROCESS TIME
##    (dominated by a ~3.46s fixed startup floor), not the catalog's
##    "1-5 seconds of USEFUL FIXED WORK" (workload-catalog.tsv's
##    calibration_rule for W03/W05/W11). The actual useful work at the
##    OLD frozen sizes was only 0.26-0.84s -- under the 1s minimum, and
##    small enough that most of every C/B0 ratio in the BP07 pilot was
##    diluted by the shared, condition-independent startup floor rather
##    than reflecting real per-work overhead. Fixed: this file now
##    writes an in-process work-time marker (Time.get_ticks_usec() around
##    the fixed-work call only, excluding process/engine startup) to a
##    file in the scratch project (see _write_work_time -- a print()
##    marker doesn't survive gd-tools' own stdout filtering), which
##    run_condition.py reads into a new work_time_seconds field --
##    calibrate.py now targets THIS metric, not process_interval_seconds,
##    and the sizes below have been re-frozen against it (see
##    calibration_result.json's post-fix entries).
## 2. W03's and W11's behavior checks only verified shape ("result has
##    5 keys", "final_state has a score key"), not the catalog's
##    required "known arm counts"/"known checkpoints and final state".
##    A bug that shifted every bucket count or every final score by a
##    constant would have passed silently. Fixed: run_condition.py now
##    computes each run's expected result INDEPENDENTLY in Python
##    (verify_workloads.py's w03_reference/w11_reference, already used
##    to correctness-check the raw engine with no coverage tool
##    involved) and passes it via a file in the scratch project
##    (expected_w03.json / expected_w11.json) -- this file now asserts exact equality
##    against that independent oracle, for calibration probes and the
##    final frozen size alike, not just the shipped default. JSON
##    numbers decode as float in GDScript (confirmed: Dictionary/Array
##    equality is NOT type-coercing between int and float even though
##    scalar `==` is -- `{"low":5.0} == {"low":5}` is false), so each
##    field is compared with an explicit int() cast rather than a whole-
##    dict `==`.
##
## FROZEN 2026-09-20 (THIRD calibration pass -- see above for what the
## first two got wrong: pass one measured zero tests at all due to an
## unrelated harness bug; pass two measured real total process time but
## against the wrong target metric).

const DEFAULT_W03_N := 15667413
const DEFAULT_W05_N_LISTENERS := 50
const DEFAULT_W05_N_DIRECT := 140701
const DEFAULT_W05_N_DEFERRED := 140701
const DEFAULT_W11_N_STEPS := 1671580
const DEFAULT_W11_SEED := 12345


static func _env_int(name: String, default_value: int) -> int:
	var v := OS.get_environment(name)
	return int(v) if not v.is_empty() else default_value


static func _write_work_time(workload: String, elapsed_usec: int) -> void:
	# A print()-based marker doesn't work here: gd-tools' CLI filters/
	# discards the child Godot process's raw stdout/stderr entirely and
	# only surfaces its own formatted summary table (confirmed directly
	# -- a WORK_TIME_USEC print never appeared in run_condition.py's
	# captured stdout even though the test itself passed). Writing to a
	# file inside the scratch project sidesteps that filtering and works
	# identically for both runners.
	var f := FileAccess.open("res://work_time_%s.txt" % workload, FileAccess.WRITE)
	f.store_string(str(elapsed_usec))
	f.close()


static func _read_expected_json(workload: String) -> String:
	# A large-n W11 probe's expected JSON can reach ~270KB (~32,000
	# milestones) -- too large for an environment variable (Linux's
	# MAX_ARG_STRLEN, 128KB, confirmed hit directly during
	# recalibration), so run_condition.py writes it to a file instead.
	var path := "res://expected_%s.json" % workload
	if not FileAccess.file_exists(path):
		return ""
	var f := FileAccess.open(path, FileAccess.READ)
	var content := f.get_as_text()
	f.close()
	return content


func test_w01() -> void:
	var subject = load("res://workloads/w01_empty_app/subject.gd")
	assert_eq(subject.run(), 42)


func test_w03() -> void:
	var n := _env_int("PERF_W03_N", DEFAULT_W03_N)
	var subject = load("res://workloads/w03_branch_heavy/subject.gd")

	var start_usec := Time.get_ticks_usec()
	var result: Dictionary = subject.run(n)
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w03", elapsed_usec)

	var expected_json := _read_expected_json("w03")
	if not expected_json.is_empty():
		var expected: Dictionary = JSON.parse_string(expected_json)
		for key in ["low", "mid_low", "mid_high", "high", "very_high"]:
			assert_eq(result.get(key, -1), int(expected[key]), "bucket '%s' mismatch" % key)
	else:
		assert_true(result.size() == 5)


func test_w05() -> void:
	var n_listeners := _env_int("PERF_W05_N_LISTENERS", DEFAULT_W05_N_LISTENERS)
	var n_direct := _env_int("PERF_W05_N_DIRECT", DEFAULT_W05_N_DIRECT)
	var n_deferred := _env_int("PERF_W05_N_DEFERRED", DEFAULT_W05_N_DEFERRED)
	var subject = load("res://workloads/w05_signals/subject.gd").new()

	var start_usec := Time.get_ticks_usec()
	subject.setup(n_listeners)
	subject.emit_direct(n_direct)
	subject.emit_deferred(n_deferred)
	await get_tree().process_frame
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w05", elapsed_usec)

	assert_eq(subject.total_delivered(), n_listeners * (n_direct + n_deferred))


func test_w11() -> void:
	var n_steps := _env_int("PERF_W11_N_STEPS", DEFAULT_W11_N_STEPS)
	var seed_value := _env_int("PERF_W11_SEED", DEFAULT_W11_SEED)
	var subject = load("res://workloads/w11_scene_app/subject.gd").new()
	add_child(subject)

	var start_usec := Time.get_ticks_usec()
	await subject.run_scenario(n_steps, seed_value)
	var elapsed_usec := Time.get_ticks_usec() - start_usec
	_write_work_time("w11", elapsed_usec)

	var final: Dictionary = subject.final_state()
	var expected_json := _read_expected_json("w11")
	if not expected_json.is_empty():
		var expected: Dictionary = JSON.parse_string(expected_json)
		assert_eq(final.get("score", null), int(expected["score"]), "score mismatch")
		assert_eq(final.get("health", null), int(expected["health"]), "health mismatch")
		assert_eq(final.get("log_length", null), int(expected["log_length"]), "log_length mismatch")
		var expected_milestones: Array = expected["milestones"]
		var actual_milestones: Array = final.get("milestones", [])
		assert_eq(actual_milestones.size(), expected_milestones.size(), "milestones length mismatch")
		for i in range(min(actual_milestones.size(), expected_milestones.size())):
			assert_eq(actual_milestones[i], int(expected_milestones[i]), "milestone[%d] mismatch" % i)
	else:
		assert_true(final.has("score"))

	remove_child(subject)
	subject.free()
