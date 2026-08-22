#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
for rel in ("systems/equipment_system.py","db_modules/shop.py","handlers/player_interaction.py"):
    source=(R/rel).read_text(encoding="utf-8");ast.parse(source)
    assert source.count("ROM 17.18.2.5 BOW CROSSBOW DAMAGE UI PARITY")==1,rel
from systems.equipment_system import get_effective_weapon_display_range_17_18_2_5 as effective
assert effective(100,200,"bow_2h")== (105,190)
assert effective(100,200,"crossbow_2h")== (85,230)
assert effective(100,200,"sword_1h")== (100,200)
assert effective(1,2,"bow_2h")== (1,2)
assert effective(1,2,"crossbow_2h")== (1,2)
shop=(R/"db_modules/shop.py").read_text(encoding="utf-8")
assert "COALESCE(item_subtype, '')" in shop and "display_min, display_max" in shop
trade=(R/"handlers/player_interaction.py").read_text(encoding="utf-8")
assert 'snapshot.get("item_subtype")' in trade
combat=(R/"systems/combat_system.py").read_text(encoding="utf-8")
assert "weapon_min_damage * 1.05" in combat and "weapon_max_damage * 1.15" in combat
print("[PASS] Stage 17.18.2.5 bow/crossbow damage UI parity contract")
