extends RefCounted
## Deliberately does not match GUT's "test_*.gd" naming convention, so a
## selection scoped to this directory has a real, populated directory to
## select from but zero files GUT will recognize as tests -- as opposed
## to an ambiguous empty directory.


static func not_a_test_helper() -> int:
	return 0
