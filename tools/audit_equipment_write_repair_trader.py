#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i6d: post-cleanup Equipment write/repair/trader audit."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGETS = (
    "equip_inventory_item", "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change", "calculate_repair_cost",
    "repair_equipped_item", "repair_all_equipped",
    "damage_equipped_items_on_death", "sell_inventory_item_to_trader",
    "buy_item_for_gold", "buy_common_equipment_from_trader",
)
REPORT = ROOT / "DB_CLEANUP_9_0_12I6D_EQUIPMENT_WRITE_REPAIR_TRADER_PHYSICAL_CLEANUP.md"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(path))
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.setdefault(node.name, []).append(node)
    return text, definitions


def safe(function, *args, **kwargs):
    try:
        return True, function(*args, **kwargs)
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
        if not system_defs.get(name):
            fail(f"equipment_system.py missing {name}")
        wrapper = ast.get_source_segment(db_text, db_defs[name][0]) or ""
        system_final = ast.get_source_segment(system_text, system_defs[name][-1]) or ""
        if "equipment_system" not in wrapper:
            fail(f"db.{name} is not an Equipment System wrapper")
        if "_call_legacy" in system_final:
            fail(f"final equipment_system.{name} still calls _call_legacy")

    repair_cases = 0
    for durability in (-10, 0, 1, 50, 99, 100, 120, None):
        for rarity in ("common", "uncommon", "rare", "epic", None):
            public = safe(db.calculate_repair_cost, durability, rarity)
            direct = safe(equipment.calculate_repair_cost, durability, rarity)
            if public != direct:
                fail(f"repair-cost mismatch: durability={durability}, rarity={rarity}")
            repair_cases += 1

    missing_uid = -987654321
    missing_iid = -987654322
    before_users = db.cursor.execute(
        "SELECT COUNT(*) FROM users WHERE user_id=?", (missing_uid,)
    ).fetchone()[0]
    before_inventory = db.cursor.execute(
        "SELECT COUNT(*) FROM inventory WHERE id=? OR user_id=?",
        (missing_iid, missing_uid),
    ).fetchone()[0]

    protected_cases = (
        ("equip_inventory_item", (missing_uid, missing_iid), {}),
        ("unequip_inventory_item", (missing_uid, missing_iid), {}),
        ("unequip_incompatible_items_after_class_change", (missing_uid,), {}),
        ("repair_equipped_item", (missing_uid, missing_iid), {}),
        ("repair_all_equipped", (missing_uid,), {}),
        ("damage_equipped_items_on_death", (missing_uid,), {}),
        ("sell_inventory_item_to_trader", (missing_uid, missing_iid), {}),
        ("buy_item_for_gold", (missing_uid, missing_iid, 10.0), {}),
        ("buy_common_equipment_from_trader", (missing_uid, "__invalid_slot__"), {}),
    )
    protected = 0
    for name, args, kwargs in protected_cases:
        public = safe(getattr(db, name), *args, **kwargs)
        direct = safe(getattr(equipment, name), *args, **kwargs)
        if public != direct:
            fail(f"protected-path mismatch {name}: public={public!r}, direct={direct!r}")
        protected += 1

    after_users = db.cursor.execute(
        "SELECT COUNT(*) FROM users WHERE user_id=?", (missing_uid,)
    ).fetchone()[0]
    after_inventory = db.cursor.execute(
        "SELECT COUNT(*) FROM inventory WHERE id=? OR user_id=?",
        (missing_iid, missing_uid),
    ).fetchone()[0]
    if (before_users, before_inventory) != (after_users, after_inventory):
        fail("protected paths changed database rows")

    report = [
        "# ROM 9.0.12i6d - Equipment Write Repair Trader Physical Cleanup",
        "",
        "## Result",
        "",
        f"- Public wrappers remaining in `db.py`: {len(TARGETS)}",
        "- Earlier definitions for these APIs remaining: 0",
        f"- Repair-cost equivalence cases: {repair_cases}",
        f"- Protected missing-ID comparisons: {protected}",
        "- Mismatches: 0",
        "- Final system `_call_legacy` dependencies: 0",
        "- Real-user mutations performed by this audit: 0",
        "",
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] equipment write/repair/trader physical cleanup audit")
    print(f"- public wrappers: {len(TARGETS)}")
    print("- earlier write/repair/trader definitions: 0")
    print(f"- repair-cost equivalence cases: {repair_cases}")
    print(f"- protected missing-ID comparisons: {protected}")
    print("- mismatches: 0")
    print("- final system legacy delegation: 0")
    print("- real user mutations: 0")
    print(f"- report: {REPORT}")


if __name__ == "__main__":
    main()
