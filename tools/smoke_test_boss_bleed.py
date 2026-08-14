from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,resolve_boss_combat_action,apply_player_effect_instruction,process_boss_player_dots

boss=build_location_boss("start_path",5,rng=random.Random(153010))
result=resolve_boss_combat_action(boss,forced_skill_key="fang_rend",actual_damage=51)
effect=result["effects"]["player_effect"]
assert effect["damage"]==10 and effect["turns"]==2 and effect["can_crit"] is False
mob={"player_effects":{}}
apply_player_effect_instruction(mob,effect)
first=process_boss_player_dots(mob,100)
assert first["current_hp"]==90 and first["damage"]==10 and not first["expired"]
second=process_boss_player_dots(mob,90)
assert second["current_hp"]==80 and second["damage"]==10 and second["expired"]==["boss_bleed"]
assert "boss_bleed" not in mob["player_effects"]
# Reapplication replaces rather than stacks.
apply_player_effect_instruction(mob,effect)
newer=dict(effect); newer["damage"]=20
apply_player_effect_instruction(mob,newer)
assert len(mob["player_effects"])==1 and mob["player_effects"]["boss_bleed"]["damage"]==20
print("[PASS] boss bleed: 20% actual damage, two ticks, no crit, replace policy")
