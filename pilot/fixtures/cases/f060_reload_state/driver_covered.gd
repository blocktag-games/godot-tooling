extends SceneTree
## Simulated coverage-collector activation: calls Script.reload(true) on
## the autoload's own script mid-run, exactly as gd-tools 0.4.0's
## addons/gd-tools-coverage/coverage.gd does to apply instrumentation to
## already-running autoloads without discarding their instances. No
## instrumentation is actually injected here -- this isolates the
## reload(true) mechanism itself from gd-tools' actual instrumentation
## step, which assigns instrumented GDScript text to the script's
## in-memory source_code property before calling reload(true) -- not a
## disk rewrite.

var ran := false


func _process(_delta: float) -> bool:
	if ran:
		return true
	ran = true
	var node = root.get_node("StatefulAutoload")
	var id_before: int = node.get_instance_id()
	node.counter += 10
	var script: Script = node.get_script()
	var reload_err: int = script.reload(true)
	var id_after: int = node.get_instance_id()
	print("reload_err=%d" % reload_err)
	print("same_instance=%s" % (id_before == id_after))
	node.counter += 100
	print("covered_final_counter=%d" % node.counter)
	return true
