#!/usr/bin/env python3
import ast, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
from data.drop_tables import DROP_RULES_BY_ID, CENTRAL_DROP_VICTORY_RULE_ORDER
from systems.drop_system import roll_central_rebirth_sphere_drop, get_victory_drop_plan, validate_drop_tables
rule = DROP_RULES_BY_ID["rebirth_sphere"]
assert rule["item_id"] == 504
assert rule["production_enabled"] is True
assert rule["mode"] == "independent"
assert rule["enemy"] == {"normal":{"chance":0.0002}, "elite":{"chance":0.001}, "boss":{"chance":0.01}}
assert rule["quantity"] == {"min":1,"max":1}
assert rule["max_per_kill"] == 1
assert rule["bag_policy"] == "stack_or_lose"
assert CENTRAL_DROP_VICTORY_RULE_ORDER[-1] == "rebirth_sphere"
assert get_victory_drop_plan()[-1] == "rebirth_sphere"
assert validate_drop_tables()["success"] is True
for mob, chance in (({},0.0002), ({"is_elite":True},0.001), ({"is_boss":True},0.01)):
    hit = roll_central_rebirth_sphere_drop(mob, lambda: chance - 1e-12)
    miss = roll_central_rebirth_sphere_drop(mob, lambda: chance)
    assert hit["rolled"] and hit["payload"]["item_id"] == 504 and hit["payload"]["quantity"] == 1
    assert not miss["rolled"] and miss["reason"] == "chance_miss"
reward = (R/"systems/reward_system.py").read_text(encoding="utf-8-sig")
ast.parse(reward)
assert 'elif rule_id == "rebirth_sphere"' in reward
assert "roll_rebirth_sphere_drop(user_id, mob)" in reward
print("[PASS] Stage 18.16.10f approved Rebirth Sphere drop contract")
