from __future__ import annotations
import ast
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
module=ROOT/"db_modules"/"generated_equipment.py"
init=ROOT/"db_modules"/"__init__.py"
for path in (module,init): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
from db import create_generated_equipment_item, create_generated_equipment_item_for_slot
assert callable(create_generated_equipment_item)
assert callable(create_generated_equipment_item_for_slot)
print("[PASS] generated equipment DB API import restored")
