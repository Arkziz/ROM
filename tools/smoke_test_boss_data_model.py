from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_DEFINITIONS,BOSS_KEY_BY_LOCATION,get_location_boss_definition
from systems.boss_system import validate_boss_definitions
assert set(BOSS_DEFINITIONS)=={"pack_leader","goblin_king"}
assert BOSS_KEY_BY_LOCATION=={"start_path":"pack_leader","dark_forest":"goblin_king"}
assert get_location_boss_definition("start_path")["name"]=="👑🐺 Ватажок Зграї"
assert get_location_boss_definition("dark_forest")["name"]=="👑👺 Король Гоблінів"
result=validate_boss_definitions()
assert result["verdict"]=="PASS",result
assert result["boss_count"]==2 and result["location_count"]==2
print("[PASS] boss data model",result)
