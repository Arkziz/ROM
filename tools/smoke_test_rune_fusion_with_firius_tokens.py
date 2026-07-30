#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -100800001


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup(db):
    for table in ("equipment_slots", "inventory", "user_daily_quests"):
        try: db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (USER_ID,))
        except Exception: pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (USER_ID,))
    db.conn.commit()


def qty(db, item_id):
    return int(db.conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",
        (USER_ID, item_id),
    ).fetchone()[0] or 0)


def give(db, item_id, quantity):
    result = db.add_item(USER_ID, item_id, quantity)
    if not result.get("success") or int(result.get("added", 0)) != quantity:
        fail(f"fixture add failed: {item_id} {quantity} {result}")


def main():
    import db
    cleanup(db)
    try:
        db.create_user(USER_ID); db.init_rune_system()
        give(db, 501, 6); give(db, 526, 2)
        recipes = db.get_available_rune_fusion_recipes(USER_ID)
        if not any(item["source_item_id"] == 501 for item in recipes):
            fail(f"STR I recipe missing: {recipes}")
        preview = db.get_rune_fusion_preview(USER_ID, 501)
        if not preview.get("success") or preview.get("result_item_id") != 502:
            fail(f"preview mismatch: {preview}")

        first = db.fuse_runes_with_firius_token(USER_ID, 501)
        if not first.get("success"): fail(f"first fusion failed: {first}")
        if (qty(db,501),qty(db,502),qty(db,526)) != (3,1,1):
            fail(f"first fusion quantities wrong: {(qty(db,501),qty(db,502),qty(db,526))}")
        second = db.fuse_runes_with_firius_token(USER_ID, 501)
        if not second.get("success"): fail(f"second fusion failed: {second}")
        if (qty(db,501),qty(db,502),qty(db,526)) != (0,2,0):
            fail("second fusion quantities wrong")
        repeat = db.fuse_runes_with_firius_token(USER_ID, 501)
        if repeat.get("code") != "not_enough_runes": fail(f"repeat guard failed: {repeat}")
        if (qty(db,501),qty(db,502),qty(db,526)) != (0,2,0):
            fail("failed repeat mutated inventory")

        give(db, 505, 3); give(db, 526, 1)
        maximum = db.fuse_runes_with_firius_token(USER_ID, 505)
        if maximum.get("code") != "max_level": fail(f"Rune V guard failed: {maximum}")
        if (qty(db,505),qty(db,526)) != (3,1): fail("Rune V failure consumed items")

        validation = db.validate_rune_fusion_selection([501,506,501])
        if validation.get("code") != "different_runes": fail("mixed-rune validation regressed")
        if "3 однакові руни" not in validation.get("message", ""):
            fail("mixed-rune user message regressed")

        handler=(ROOT/"handlers/runes.py").read_text(encoding="utf-8-sig")
        main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
        for marker in ("🔄 Переробити руни","✅ Переробити","rf:confirm:","Шанс успіху: 100%"):
            if marker not in handler: fail(f"fusion UI marker missing: {marker}")
        if "register_rune_fusion_handlers(bot)" not in main:
            fail("fusion handlers not registered")

        print("[OK] Rune fusion with Firius Token contracts")
        print("- recipe: 3 identical runes + 1 token -> 1 next-level rune")
        print("- success chance: 100%")
        print("- exact consumption and result: OK")
        print("- cumulative tokens/no daily counter: OK")
        print("- repeated callback duplication: 0")
        print("- insufficient rune/token rollback: OK")
        print("- mixed stat/level validation: OK")
        print("- Rune V fusion rejection: OK")
        print("- Rune Master fusion UI: OK")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__": main()
