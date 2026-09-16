# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
contracts={
 "systems/character_system.py":["player_joined",'f"player_joined:{int(user_id)}"',"if not previous_class:"],
 "systems/player_system.py":["player_level_up",'f"player_level_up:{int(user_id)}:{int(level)}"',"if level_ups:","connection=db.conn"],
 "systems/refine_system.py":["equipment_max_refine",'f"equipment_max_refine:{inv_id}:{max_level}"',"current == max_level - 1","connection=conn"],
 "handlers/combat.py":["location_boss_defeated",'f"location_boss_defeated:{encounter_id}"','mob.get("pve_encounter_id")','if mob.get("is_boss")'],
}
for relative,needles in contracts.items():
 source=(ROOT/relative).read_text(encoding="utf-8-sig");ast.parse(source);compile(source,relative,"exec")
 for needle in needles:assert needle in source,(relative,needle)
assert "spawned_at" not in (ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")
assert "battle_id" not in (ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig")[(ROOT/"handlers/combat.py").read_text(encoding="utf-8-sig").find("location_boss_defeated")-300:]
print("WORLD_CHRONICLE_EVENTS_18_XX_13_OK")
