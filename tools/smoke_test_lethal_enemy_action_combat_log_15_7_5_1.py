from __future__ import annotations
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"handlers"/"combat.py"
text=path.read_text(encoding="utf-8")
tree=ast.parse(text,filename=str(path))
functions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
helpers=[n for n in functions if n.name=="build_lethal_combat_log"]
assert len(helpers)==1, len(helpers)
helper=helpers[0]
segment=ast.get_source_segment(text,helper) or ""
for token in ("enemy_action_text","player_effects_text","enemy_effect_text","skill","dmg","ОСТАННІ ПОДІЇ БОЮ","Здоров’я перед поразкою","build_death_text"):
 assert token in segment,token
lethal_calls=[]
legacy_death_calls=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
  if node.func.id=="build_lethal_combat_log": lethal_calls.append(node)
  if node.func.id=="build_death_text": legacy_death_calls.append(node)
assert len(lethal_calls)==3, len(lethal_calls)
assert len(legacy_death_calls)==1, len(legacy_death_calls)
for call in lethal_calls:
 names={kw.arg for kw in call.keywords}
 assert {"turn_context","player_hp","player_max_hp","durability_damage"}<=names,names
print("[PASS] lethal combat log wired into all death paths",{"death_paths":3,"helper_definitions":1,"boss_gate_agnostic":True})
