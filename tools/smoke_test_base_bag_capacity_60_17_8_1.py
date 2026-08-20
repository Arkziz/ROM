#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = {
    "db_modules/connection.py": ("DEFAULT_BAG_SLOTS = 60", "INTEGER DEFAULT 60"),
    "db_modules/inventory.py": ("max(DEFAULT_BAG_SLOTS, capacity)",),
    "db_modules/generated_equipment.py": ("max(DEFAULT_BAG_SLOTS, capacity)",),
    "db_modules/dev_compat.py": ("max(DEFAULT_BAG_SLOTS, capacity)", 'globals().get("DEFAULT_BAG_SLOTS", 60)'),
    "db_modules/migrations.py": ("def expand_bag_slots_to_60", "return expand_bag_slots_to_60()"),
    "db_modules/player.py": ("DEFAULT_BAG_SLOTS,  # ROM 17.8.1",),
    "systems/auction_house_system.py": ("return 60  # ROM 17.8.1",),
    "systems/equipment_system.py": ("COALESCE(bag_slots,60)", "max(60, int(row[0] or 60))"),
    "systems/player_interaction_system.py": ("COALESCE(bag_slots,60)", "or 60)  # ROM 17.8.1"),
    "systems/rune_system.py": ("capacity = max(60",),
}
for rel, needles in checks.items():
    source = (ROOT / rel).read_text(encoding="utf-8")
    ast.parse(source)
    for needle in needles:
        assert needle in source, (rel, needle)

connection = (ROOT / "db_modules/connection.py").read_text(encoding="utf-8")
assert "DEFAULT_BAG_SLOTS = 40" not in connection
assert "INTEGER DEFAULT 20" not in connection
inventory = (ROOT / "db_modules/inventory.py").read_text(encoding="utf-8")
assert "return max(40, capacity)" not in inventory
assert "return 40  # DEFAULT_BAG_SLOTS" not in inventory
assert "systems/simulation" not in " ".join(checks)
print("[PASS] Stage 17.8.1 base bag capacity 60 static contract")
