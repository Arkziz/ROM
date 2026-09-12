#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, copy, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
TREE=ast.parse(SOURCE)
REQUIRED={"init_combat_effects","add_enemy_effect","remove_enemy_effect","process_enemy_turn_start_effects","init_skill_cooldowns","get_skill_cooldown","set_skill_cooldown","tick_skill_cooldowns_at_player_turn","validate_skill_cooldown","roll_skill_stun"}
NODES={n.name:n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in REQUIRED}
assert set(NODES)==REQUIRED, sorted(REQUIRED-set(NODES))
module=ast.Module(body=[NODES[name] for name in REQUIRED],type_ignores=[]);ast.fix_missing_locations(module);ns={};exec(compile(module,"combat_timing_fixture","exec"),ns)
# New enemy effects are fresh: no same-turn tick and no same-turn duration loss.
mob={"hp":100};ns["add_enemy_effect"](mob,"dot",{"name":"DOT","icon":"*","type":"dot","turns":3,"damage":7,"modifiers":{}})
assert mob["enemy_effects"]["dot"]["fresh"] is True
first=ns["process_enemy_turn_start_effects"](mob);assert first["damage"]==0 and mob["hp"]==100 and mob["enemy_effects"]["dot"]["turns"]==3 and "fresh" not in mob["enemy_effects"]["dot"]
second=ns["process_enemy_turn_start_effects"](mob);assert second["damage"]==7 and mob["hp"]==93 and mob["enemy_effects"]["dot"]["turns"]==2
third=ns["process_enemy_turn_start_effects"](mob);fourth=ns["process_enemy_turn_start_effects"](mob);assert mob["hp"]==79 and "dot" not in mob["enemy_effects"]
# Reapply contract: same key never stacks; weaker/shorter does not replace; longer refreshes; stronger replaces without shortening.
mob={"hp":100};ns["add_enemy_effect"](mob,"dot",{"type":"dot","turns":3,"damage":8});ns["process_enemy_turn_start_effects"](mob)
ns["add_enemy_effect"](mob,"dot",{"type":"dot","turns":2,"damage":5});assert mob["enemy_effects"]["dot"]["turns"]==3 and mob["enemy_effects"]["dot"]["damage"]==8 and "fresh" not in mob["enemy_effects"]["dot"]
ns["add_enemy_effect"](mob,"dot",{"type":"dot","turns":5,"damage":8});assert mob["enemy_effects"]["dot"]["turns"]==5 and "fresh" not in mob["enemy_effects"]["dot"]
ns["add_enemy_effect"](mob,"dot",{"type":"dot","turns":4,"damage":12});assert mob["enemy_effects"]["dot"]["damage"]==12 and mob["enemy_effects"]["dot"]["turns"]==5 and "fresh" not in mob["enemy_effects"]["dot"]
# Cooldown N blocks exactly N subsequent player actions.
mob={};msg=ns["set_skill_cooldown"](mob,"skill",2);assert "2" in msg and ns["get_skill_cooldown"](mob,"skill")==3
skill={"key":"skill","name":"Skill"};ns["tick_skill_cooldowns_at_player_turn"](mob);assert ns["validate_skill_cooldown"](mob,skill)["success"] is False and ns["get_skill_cooldown"](mob,"skill")==2
ns["tick_skill_cooldowns_at_player_turn"](mob);assert ns["validate_skill_cooldown"](mob,skill)["success"] is False and ns["get_skill_cooldown"](mob,"skill")==1
ns["tick_skill_cooldowns_at_player_turn"](mob);assert ns["validate_skill_cooldown"](mob,skill)["success"] is True and ns["get_skill_cooldown"](mob,"skill")==0
# Stun remains immediate and consumes exactly the nearest enemy action in each canonical combat route.
assert SOURCE.count('if mob.get("stunned_turns", 0) > 0:')==3
assert SOURCE.count('mob["stunned_turns"] -= 1')==3
assert 'mob["stunned_turns"] = 1' in SOURCE
assert "systems.pvp_" not in SOURCE
print("[PASS] Stage 18.19.1 PvE fresh effects, reapply policy, stun and cooldown boundaries")
