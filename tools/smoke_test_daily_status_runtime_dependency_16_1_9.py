from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
path=ROOT/"db_modules"/"quests.py"
tree=ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="process_daily_quest_progress_on_kill")
imports=[node for node in ast.walk(fn) if isinstance(node,ast.ImportFrom) and node.module=="daily_compat"]
assert imports and any(alias.name=="get_daily_quest_status" for node in imports for alias in node.names)
from db_modules.daily_compat import get_daily_quest_status
from db_modules.quests import process_daily_quest_progress_on_kill,reset_daily_quest_if_needed
assert callable(get_daily_quest_status) and callable(process_daily_quest_progress_on_kill) and callable(reset_daily_quest_if_needed)
print("[PASS] daily status runtime dependency restored")
