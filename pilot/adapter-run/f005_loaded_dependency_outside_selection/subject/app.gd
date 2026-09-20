extends RefCounted

const Vendor = preload("res://addons/vendor_lib/vendor.gd")

static func run() -> int:
	return Vendor.run() + 1
