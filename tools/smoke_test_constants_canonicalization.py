#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only contracts for db.py constants canonicalization."""
from __future__ import annotations

import ast
import hashlib
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
CANONICAL_GROUPS = {
    "data.classes": (
        "CLASS_CONFIGS", "CLASS_RESET_SPHERE_ITEM_ID",
    ),
    "data.equipment_profiles": (
        "ARMOR_ALLOWED_BY_CLASS", "ARMOR_EXTRA_STATS_BY_SLOT",
        "ARMOR_TYPE_LABELS", "EQUIPMENT_SLOTS", "ITEM_SUBTYPE_LABELS",
        "MAIN_HAND_ALLOWED_BY_CLASS", "MAIN_HAND_PROFILES",
        "OFF_HAND_ALLOWED_BY_CLASS", "OFF_HAND_PROFILES",
    ),
    "data.balance": (
        "CONTRACTS_UNLOCK_LEVEL", "CONTRACT_MOBS_EQUIVALENT",
        "CONTRACT_TARGET_KILLS", "DAILY_CONTRACT_LIMIT",
        "DAILY_QUEST_ID_KILL_MONSTERS", "DAILY_QUEST_REWARD_ITEM_ID",
        "DAILY_QUEST_REWARD_QUANTITY", "DAILY_QUEST_TARGET_KILLS",
        "ENERGY_MAX", "ENERGY_REGEN_MINUTES", "HP_REGEN_MINUTES",
        "HP_REGEN_PERCENT", "RARITY_REPAIR_MULTIPLIERS",
        "REFINE_MATERIAL_MAX_STACK", "REFINE_STONE_ITEM_ID",
    ),
}
ALL_CONSTANTS = tuple(name for values in CANONICAL_GROUPS.values() for name in values)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def assigned_names(node):
    names = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
    return names


def main():
    before = fingerprint()
    source = DB_PY.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(DB_PY))

    local_definitions = []
    imported = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            overlap = assigned_names(node).intersection(ALL_CONSTANTS)
            if overlap:
                local_definitions.extend((name, node.lineno) for name in overlap)
        elif isinstance(node, ast.ImportFrom) and node.module in CANONICAL_GROUPS:
            for alias in node.names:
                imported[alias.asname or alias.name] = node.module

    if local_definitions:
        fail(f"local duplicate definitions remain: {local_definitions}")

    missing_imports = [
        name for module, names in CANONICAL_GROUPS.items() for name in names
        if imported.get(name) != module
    ]
    if missing_imports:
        fail(f"canonical imports missing or owned by wrong module: {missing_imports}")

    import db
    identity_checks = 0
    value_checks = 0
    for module_name, names in CANONICAL_GROUPS.items():
        canonical = importlib.import_module(module_name)
        for name in names:
            if not hasattr(db, name):
                fail(f"db public constant missing: {name}")
            if not hasattr(canonical, name):
                fail(f"canonical constant missing: {module_name}.{name}")
            db_value = getattr(db, name)
            canonical_value = getattr(canonical, name)
            if db_value != canonical_value:
                fail(f"value mismatch: db.{name} != {module_name}.{name}")
            value_checks += 1
            if isinstance(canonical_value, (dict, list, set)):
                if db_value is not canonical_value:
                    fail(f"identity mismatch for mutable canonical object: {name}")
                identity_checks += 1

    required_runtime = {
        "class_name": db.get_class_display_name_by_key("mage"),
        "armor_label": db.get_armor_type_label("cloth"),
        "subtype_label": db.get_item_subtype_label("sword_1h"),
        "repair_multiplier": db.get_rarity_repair_multiplier("epic"),
        "contract_exp": db.get_contract_exp_for_level(10),
    }
    if not required_runtime["class_name"] or not required_runtime["armor_label"]:
        fail(f"runtime helper output invalid: {required_runtime}")

    if before != fingerprint():
        fail("game.db changed during read-only contracts")

    print("[OK] constants canonicalization contracts")
    print(f"- local duplicate definitions: {len(local_definitions)}")
    print(f"- canonical imports verified: {value_checks}")
    print(f"- mutable object identity checks: {identity_checks}")
    print(f"- public db constant surface preserved: {len(ALL_CONSTANTS)}")
    print(f"- runtime helper probes: {required_runtime}")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
