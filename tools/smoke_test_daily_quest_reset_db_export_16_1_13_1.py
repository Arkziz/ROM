from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db
from db_modules.quests import reset_daily_quest_if_needed as canonical
assert hasattr(db,"reset_daily_quest_if_needed")
assert callable(db.reset_daily_quest_if_needed)
assert db.reset_daily_quest_if_needed is canonical
import systems.rune_system as rune_system
assert rune_system._db().reset_daily_quest_if_needed is canonical
print("[PASS] daily quest reset exported through db facade")
