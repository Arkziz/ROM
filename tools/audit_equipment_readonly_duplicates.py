#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6b: verify Equipment read-only physical cleanup."""
from __future__ import annotations
import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "ensure_equipment_slots", "get_all_equipped_items", "get_inventory_detailed",
    "get_inventory_entry", "get_item_by_inventory_id", "get_item_by_inventory_id_full",
    "get_item_bonuses", "get_equipped_item_defenses", "get_sellable_equipment_items",
    "get_inventory_refine_level", "get_inventory_refined_display_name",
    "format_refined_item_name", "init_weapon_damage_system",
    "calculate_weapon_damage_by_values", "get_weapon_damage_by_inventory_id",
    "get_inventory_weapon_damage_display",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I6B_EQUIPMENT_READONLY_PHYSICAL_CLEANUP.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return text, result


def safe(function, *args):
    try:
        return True, function(*args)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main():
    db_text, db_defs = parse(ROOT / "db.py")
    system_text, system_defs = parse(ROOT / "systems" / "equipment_system.py")

    import db
    from systems import equipment_system as equipment

    for name in TARGETS:
        if len(db_defs.get(name, [])) != 1:
            fail(f"db.py {name}: definitions={len(db_defs.get(name, []))}, expected 1")
        if len(system_defs.get(name, [])) < 1:
            fail(f"equipment_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        system = ast.get_source_segment(system_text, system_defs[name][-1]) or ""
        if "equipment_system" not in wrapper:
            fail(f"db.{name} is not an Equipment System wrapper")
        if "_call_legacy" in system:
            fail(f"final equipment_system.{name} still calls _call_legacy")

    users = [int(row[0]) for row in db.cursor.execute("SELECT user_id FROM users ORDER BY user_id").fetchall()]
    comparisons = 0
    for user_id in users:
        for name in (
            "get_all_equipped_items", "get_inventory_detailed", "get_item_bonuses",
            "get_equipped_item_defenses", "get_sellable_equipment_items",
        ):
            if safe(getattr(db, name), user_id) != safe(getattr(equipment, name), user_id):
                fail(f"user comparison mismatch: {name}, user={user_id}")
            comparisons += 1

        inventory_rows = db.cursor.execute(
            "SELECT id FROM inventory WHERE user_id=? ORDER BY id LIMIT 20", (user_id,)
        ).fetchall()
        for (inventory_id,) in inventory_rows:
            for name in (
                "get_inventory_entry", "get_item_by_inventory_id",
                "get_item_by_inventory_id_full", "get_inventory_refine_level",
                "get_inventory_refined_display_name", "get_weapon_damage_by_inventory_id",
                "get_inventory_weapon_damage_display",
            ):
                if safe(getattr(db, name), inventory_id) != safe(getattr(equipment, name), inventory_id):
                    fail(f"item comparison mismatch: {name}, inventory={inventory_id}")
                comparisons += 1

    pure_cases = (
        ("calculate_weapon_damage_by_values", (8, 12, 1, "common")),
        ("format_refined_item_name", ("Item", 3)),
    )
    for name, args in pure_cases:
        if safe(getattr(db, name), *args) != safe(getattr(equipment, name), *args):
            fail(f"pure API mismatch: {name}")

    report = [
        "# ROM 9.0.12i6b - Equipment Read-only Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Public Equipment wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier definitions for these APIs remaining: 0",
        f"- Public/system read-only comparisons: {comparisons}",
        f"- Pure API comparisons: {len(pure_cases)}",
        "- Mismatches: 0",
        "- Final system `_call_legacy` dependencies: 0",
        "- Database mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] equipment read-only physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier Equipment read-only definitions: 0")
    print(f"- public/system comparisons: {comparisons}")
    print(f"- pure API comparisons: {len(pure_cases)}")
    print("- mismatches: 0")
    print("- final system legacy delegation: 0")
    print("- database mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
