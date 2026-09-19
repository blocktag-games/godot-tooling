extends SceneTree
## Uninstrumented baseline: no reload() call. Establishes the expected
## final state with nothing that could disturb it.

var ran := false


func _process(_delta: float) -> bool:
	if ran:
		return true
	ran = true
	var node = root.get_node("StatefulAutoload")
	node.counter += 10
	node.counter += 100
	print("baseline_final_counter=%d" % node.counter)
	return true
