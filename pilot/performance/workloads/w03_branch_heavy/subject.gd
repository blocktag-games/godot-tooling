extends RefCounted
## W03: Branch-heavy deterministic logic. A fixed decision count (n)
## over a predefined, FORMULA-GENERATED input sequence -- not true
## randomness, so the exact sequence and its per-branch outcome are
## independently reproducible without storing a literal array -- run
## through a 5-way if/elif chain. Final state (per-branch counts) is
## checkable against an independent re-implementation of the same
## classification (see verify_workloads.py), the same pattern as W02's
## analytic checksum.

static func run(n: int) -> Dictionary:
	var counts := {"low": 0, "mid_low": 0, "mid_high": 0, "high": 0, "very_high": 0}
	for i in range(n):
		var v: int = (i * 2654435761) % 1000
		if v < 100:
			counts["low"] += 1
		elif v < 400:
			counts["mid_low"] += 1
		elif v < 700:
			counts["mid_high"] += 1
		elif v < 950:
			counts["high"] += 1
		else:
			counts["very_high"] += 1
	return counts
