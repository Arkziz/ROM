#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for rel in ("systems/attribute_respec_system.py","systems/character_system.py","db_modules/inventory_compat.py","handlers/start.py"):
 ast.parse((R/rel).read_text(encoding="utf-8-sig"))
r=(R/"systems/attribute_respec_system.py").read_text(encoding="utf-8-sig")
c=(R/"systems/character_system.py").read_text(encoding="utf-8-sig")
i=(R/"db_modules/inventory_compat.py").read_text(encoding="utf-8-sig")
s=(R/"handlers/start.py").read_text(encoding="utf-8-sig")
assert "expected_item_id" in r and "source_item_id" in r
assert "CLASS_RESET_SPHERE_ITEM_ID" in c and "pending_class_change_inventory_id" in c
assert "DELETE FROM inventory" not in ast.get_source_segment(i, [n for n in ast.parse(i).body if isinstance(n,ast.FunctionDef) and n.name=="use_class_reset_sphere_from_inventory"][0])
assert "pending_class_change_inventory_id" in i
assert "Буде повернено очок характеристик" in s
assert "Сфера нового шляху буде витрачена лише після підтвердження" in s
print("[PASS] Stage 18.16.9 atomic New Path Sphere structural contract")
