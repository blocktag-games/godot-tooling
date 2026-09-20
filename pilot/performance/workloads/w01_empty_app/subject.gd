extends RefCounted
## W01: Empty Godot application. Deliberately the smallest possible
## "valid sentinel action" per docs/benchmarks/workload-catalog.tsv's
## calibration_rule ("No artificial useful-work expansion") -- this
## workload measures startup/instrumentation/teardown overhead, not
## application work, so padding it with busy-work would defeat its
## purpose.

static func run() -> int:
	return 6 * 7
