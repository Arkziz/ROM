#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));DB=ROOT/"game.db"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
before=sha(DB)
for rel in ("handlers/combat.py","keyboards.py","systems/pve_skill_action_state.py"):
 s=(ROOT/rel).read_text(encoding="utf-8");ast.parse(s);assert s.count("ROM 17.16.1 PVE SKILL BUTTON STATES")==1,rel
from systems.pve_skill_action_state import get_pve_skill_action_state as state
base={"skill_cooldowns":{},"player_effects":{},"player_rage":0,"player_combat_energy":0,"player_max_combat_energy":100,"player_combo_points":0,"player_mp":10}
def skill(key="x",cost_type="mana",cost=25,**kw):return {"key":key,"name":"Test","cost_type":cost_type,"cost":cost,**kw}
assert state(1,{**base,"skill_cooldowns":{"x":2}},skill())["reason"]=="cooldown"
assert state(1,{**base,"player_stunned_turns":1},skill())["reason"]=="control_state"
assert state(1,base,skill())["reason"]=="not_enough_mana"
assert state(1,{**base,"player_rage":10},skill(cost_type="rage",cost=30))["reason"]=="not_enough_rage"
assert state(1,{**base,"player_combat_energy":0},skill(cost_type="combat_energy",cost=25))["reason"]=="not_enough_combat_energy"
assert state(1,{**base,"player_combat_energy":5},skill(cost_type="combat_energy",cost=25))["available"]
assert state(1,{**base,"player_combat_energy":100,"player_combo_points":0},skill(cost_type="combat_energy_combo",cost=20,min_combo=1))["reason"]=="not_enough_combo"
assert state(1,{**base,"player_mp":30},skill())["available"]
combat=(ROOT/"handlers/combat.py").read_text(encoding="utf-8")
tree=ast.parse(combat)
locked=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="skill_locked"][-1]
ls=ast.get_source_segment(combat,locked) or ""
for forbidden in ("validate_and_pay_skill_cost","set_skill_cooldown","tick_skill_cooldowns_at_player_turn","process_enemy_turn_start_effects","send_message"):
 assert forbidden not in ls,forbidden
assert "get_pve_skill_action_state" in ls and "show_alert=True" in ls
assert "validate_skill_cooldown" in combat and "validate_and_pay_skill_cost" in combat
assert sha(DB)==before
print("[PASS] Stage 17.16.1 PvE skill button-state contract")
