from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/overlevel_policy.py",ROOT/"rom_v2/application/overlevel_policy_service.py",ROOT/"rom_v2/presentation/overlevel_policy.py"]
for p in files:ast.parse(p.read_text(encoding="utf-8"))
text="\n".join(p.read_text(encoding="utf-8") for p in files)
for bad in ("from handlers.","from db_modules.","import sqlite3","import aiogram","commit("):
 if bad in text:print("Overlevel policy boundary: FAIL",bad);sys.exit(1)
for mark in ("current_level)>int(max_levels[location_id])","reward_claimed:bool=False","quest_items","atomic(self)"):
 if mark not in text:print("Overlevel policy contract marker: FAIL",mark);sys.exit(1)
print("Stage 21.13.7c Overlevel policy boundary: PASS")
