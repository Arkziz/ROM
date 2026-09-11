#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from data.equipment_stat_policy import (
    CLASS_ARMOR_TYPES, CLASS_MAIN_HAND_SUBTYPES, CLASS_OFF_HAND_SUBTYPES,
    get_allowed_equipment_stats, get_equipment_stat_weights,
    normalize_equipment_class, validate_equipment_stat_policy,
)
CLASSES=("warrior","knight","rogue","scout","mage","priest")
assert validate_equipment_stat_policy()==()
assert set(CLASS_ARMOR_TYPES)==set(CLASSES)
assert CLASS_ARMOR_TYPES=={"mage":"cloth","priest":"cloth","scout":"leather","rogue":"leather","warrior":"chain","knight":"plate"}
for cls in CLASSES:
    for kind in ("weapon","armor","jewelry"):
        profile=get_equipment_stat_weights(cls,kind)
        assert sum(weight for _stat,weight in profile)==100
        assert len({stat for stat,_weight in profile})==len(profile)
    for subtype in CLASS_MAIN_HAND_SUBTYPES[cls]:
        assert get_equipment_stat_weights(cls,"weapon",item_subtype=subtype)
    for subtype in CLASS_OFF_HAND_SUBTYPES[cls]:
        assert get_equipment_stat_weights(cls,"off_hand",item_subtype=subtype)
assert get_allowed_equipment_stats("knight","off_hand",item_subtype="shield")==("sta","str")
assert "wis" not in get_allowed_equipment_stats("knight","off_hand",item_subtype="shield")
assert get_allowed_equipment_stats("mage","armor") == ("int","wis","sta")
assert get_allowed_equipment_stats("priest","armor") == ("int","wis","sta")
assert dict(get_equipment_stat_weights("mage","armor"))["int"] > dict(get_equipment_stat_weights("mage","armor"))["wis"]
assert dict(get_equipment_stat_weights("priest","armor"))["wis"] > dict(get_equipment_stat_weights("mage","armor"))["wis"]
assert dict(get_equipment_stat_weights("scout","armor"))["str"] == dict(get_equipment_stat_weights("scout","armor"))["dex"]
assert dict(get_equipment_stat_weights("rogue","armor"))["dex"] > dict(get_equipment_stat_weights("rogue","armor"))["str"]
for cls in ("warrior","knight"):
    stats=get_allowed_equipment_stats(cls,"weapon")
    assert stats[0]=="str" and "dex" in stats and "sta" in stats
for cls in ("warrior","knight","scout","rogue"):
    assert not ({"int","wis"}&set(get_allowed_equipment_stats(cls,"jewelry")))
for cls in ("mage","priest"):
    assert not ({"str","dex"}&set(get_allowed_equipment_stats(cls,"jewelry")))
try:normalize_equipment_class("unknown")
except ValueError:pass
else:raise AssertionError("unknown class must fail closed")
try:get_equipment_stat_weights("knight","off_hand",item_subtype="talisman")
except ValueError:pass
else:raise AssertionError("invalid subtype must fail closed")
# Runtime-owner guard: policy is pure; production integration is intentionally deferred.
policy=(R/"data/equipment_stat_policy.py").read_text(encoding="utf-8-sig")
assert not any(token in policy for token in ("sqlite3","INSERT ","UPDATE ","DELETE ","cursor.","conn."))
gen=ast.parse((R/"db_modules/generated_equipment.py").read_text(encoding="utf-8-sig"))
dyn=ast.parse((R/"systems/dynamic_equipment_system.py").read_text(encoding="utf-8-sig"))
gen_names={n.name for n in gen.body if isinstance(n,ast.FunctionDef)}
dyn_names={n.name for n in dyn.body if isinstance(n,ast.FunctionDef)}
assert {"create_generated_equipment_item","create_generated_equipment_item_for_slot"} <= gen_names
assert "create_generated_equipment_item" not in dyn_names
assert "create_generated_equipment_item_for_slot" not in dyn_names
print("[PASS] Stage 18.17.1 canonical class-aware equipment stat policy")
