extends RefCounted
## W11's "resource access" element: a small dependency loaded (not
## preloaded, so it exercises the same load() path F049 verified) by
## the scenario driver each run, rather than inlining its lookup table
## directly into run_scenario().

static func score_delta(v: int) -> int:
	if v < 10:
		return -5
	elif v < 60:
		return 1
	else:
		return 3
