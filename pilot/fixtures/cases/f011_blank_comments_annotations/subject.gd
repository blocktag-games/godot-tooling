extends RefCounted

## Doc comment, not executable.
# Regular comment, not executable.

@warning_ignore("integer_division")
static func run(x: int) -> int:
	# Inline comment before a statement, not executable.
	var doubled: int = x * 2  # trailing comment, line is still executable
	return doubled
