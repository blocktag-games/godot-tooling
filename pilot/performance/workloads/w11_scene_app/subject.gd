extends Node
## W11: Representative scene application. A fixed-step (n_steps),
## fixed-seed scenario combining state mutation, a signal, a resource
## load, and one await point -- the combination of mechanisms BP06's
## lifecycle domain fixtures (F042-F049) individually verified in
## isolation, now exercised together as one representative workload.
## Final state (score, health, milestones, log_length) and the overall
## trajectory are independently computable from n_steps and seed_value,
## since the per-step event is a deterministic formula, not true
## randomness (see verify_workloads.py's Python reference
## implementation).

signal milestone_reached(score: int)

var score: int = 0
var health: int = 100
var event_log: Array = []
var milestones_seen: Array = []


func _ready() -> void:
	milestone_reached.connect(_on_milestone)


func _on_milestone(score_value: int) -> void:
	milestones_seen.append(score_value)


func run_scenario(n_steps: int, seed_value: int) -> void:
	var scoring = load("res://workloads/w11_scene_app/scoring_table.gd")
	for step in range(n_steps):
		var v: int = (step * 2654435761 + seed_value) % 100
		var delta: int = scoring.score_delta(v)
		score += delta
		if v < 10:
			health -= 1
		event_log.append(delta)
		if score > 0 and score % 50 == 0 and not milestones_seen.has(score):
			milestone_reached.emit(score)
		if step == int(n_steps / 2):
			await Engine.get_main_loop().process_frame


func final_state() -> Dictionary:
	return {
		"score": score,
		"health": health,
		"milestones": milestones_seen,
		"log_length": event_log.size(),
	}
