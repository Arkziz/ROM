#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i11a: remove safe orphaned rows left by known negative test fixtures."""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i11a"
KNOWN_FIXTURE_IDS = {
    -987654321,  # historical smoke-test fixture: 10 empty equipment slots
    -90120701,
    -90120901,
    -90121001,
    -90121002,
    -90121011,
    -90121012,
    -90121013,
    -90121021,
    -90121022,
    -90121023,
}


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (root / "db.py").is_file() and (root / "tools" / "db_cleanup_readiness.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def table_columns(conn, table):
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}


def main():
    root = find_root()
    sys.path.insert(0, str(root))
    import db

    conn = db.conn
    placeholders = ",".join("?" for _ in KNOWN_FIXTURE_IDS)
    fixture_ids = tuple(sorted(KNOWN_FIXTURE_IDS))

    if not {"user_id", "slot_key", "inventory_id"}.issubset(table_columns(conn, "equipment_slots")):
        fail("Таблиця equipment_slots має неочікувану схему.")

    rows = conn.execute(
        f"""SELECT es.user_id, es.slot_key, es.inventory_id,
                   CASE WHEN u.user_id IS NULL THEN 0 ELSE 1 END AS user_exists
            FROM equipment_slots es
            LEFT JOIN users u ON u.user_id=es.user_id
            WHERE es.user_id<0
            ORDER BY es.user_id, es.slot_key"""
    ).fetchall()

    unknown = [tuple(row) for row in rows if int(row[0]) not in KNOWN_FIXTURE_IDS]
    if unknown:
        fail(f"Знайдено невідомі negative-ID equipment_slots; автоматичне видалення заборонено: {unknown}")

    unsafe = [tuple(row) for row in rows if int(row[3]) != 0 or row[2] is not None]
    if unsafe:
        fail(f"Знайдено negative fixture rows із користувачем або inventory_id; автоматичне видалення заборонено: {unsafe}")

    before_count = len(rows)
    affected_ids = sorted({int(row[0]) for row in rows})

    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            f"""DELETE FROM equipment_slots
                WHERE user_id IN ({placeholders})
                  AND user_id<0
                  AND inventory_id IS NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM users u WHERE u.user_id=equipment_slots.user_id
                  )""",
            fixture_ids,
        )
        deleted = int(conn.execute("SELECT changes()").fetchone()[0] or 0)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        fail(f"Cleanup transaction rolled back: {exc}")

    remaining = int(
        conn.execute("SELECT COUNT(*) FROM equipment_slots WHERE user_id<0").fetchone()[0] or 0
    )
    if remaining != 0:
        fail(f"Після cleanup залишилися negative-ID equipment_slots: {remaining}")
    if deleted != before_count:
        fail(f"Видалено {deleted}, очікувалося {before_count}; потрібна ручна перевірка.")

    report = root / "DB_CLEANUP_9_0_12I11A_FIXTURE_RESIDUE_CLEANUP.md"
    report.write_text(
        "\n".join([
            "# ROM 9.0.12i11a - Fixture Residue Cleanup",
            "",
            f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
            "",
            f"- Known orphan fixture rows found: **{before_count}**",
            f"- Fixture user IDs: **{affected_ids}**",
            f"- Rows deleted: **{deleted}**",
            "- Real users deleted or changed: **0**",
            "- Inventory-linked equipment slots deleted: **0**",
            "- Unknown negative IDs deleted: **0**",
            "- Transaction committed: **yes**",
            "",
        ]),
        encoding="utf-8",
    )

    print("[OK] known fixture residue cleanup")
    print(f"- orphan equipment_slots found: {before_count}")
    print(f"- fixture user IDs: {affected_ids}")
    print(f"- rows deleted: {deleted}")
    print("- real user mutations: 0")
    print("- inventory-linked rows deleted: 0")
    print("- unknown negative IDs deleted: 0")
    print(f"- report: {report}")
    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("Повторна перевірка:")
    print("   python ./patch/patch_9_0_12i11_final_closure_audit.py")


if __name__ == "__main__":
    main()
