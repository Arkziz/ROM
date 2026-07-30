#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 10.3.0: award 10 cumulative Firius Tokens with Daily Quest claim."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "10.3.0"
SYSTEM_REL = Path("systems/rune_system.py")
DB_REL = Path("db.py")
HANDLER_REL = Path("handlers/daily.py")
TEST_REL = Path("tools/smoke_test_daily_firius_token_reward.py")

SYSTEM_APPEND = r'''

# ==============================
# ROM 10.3.0 DAILY QUEST FIRIUS TOKEN REWARD
# ==============================


def _plan_stack_addition(conn, user_id, item_id, quantity):
    """Build a no-write stack plan and required new-slot count."""
    quantity = int(quantity)
    row = conn.execute(
        "SELECT name, max_stack FROM items WHERE id=?", (int(item_id),)
    ).fetchone()
    if not row:
        raise RuntimeError(f"Reward item does not exist: {item_id}")
    name = str(row[0])
    max_stack = max(1, int(row[1] or 1))
    stacks = conn.execute(
        "SELECT id, quantity FROM inventory "
        "WHERE user_id=? AND item_id=? ORDER BY id",
        (int(user_id), int(item_id)),
    ).fetchall()
    remaining = quantity
    updates = []
    for inventory_id, current in stacks:
        current = int(current or 0)
        free = max(0, max_stack - current)
        if free <= 0:
            continue
        add = min(free, remaining)
        updates.append((current + add, int(inventory_id)))
        remaining -= add
        if remaining <= 0:
            break
    inserts = []
    while remaining > 0:
        add = min(max_stack, remaining)
        inserts.append(add)
        remaining -= add
    return {
        "item_id": int(item_id),
        "name": name,
        "quantity": quantity,
        "updates": updates,
        "inserts": inserts,
        "new_slots": len(inserts),
    }


def _apply_stack_plan(conn, user_id, plan):
    for new_quantity, inventory_id in plan["updates"]:
        conn.execute(
            "UPDATE inventory SET quantity=? WHERE id=? AND user_id=?",
            (new_quantity, inventory_id, int(user_id)),
        )
    for quantity in plan["inserts"]:
        conn.execute(
            "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
            (int(user_id), plan["item_id"], quantity),
        )


def claim_daily_quest_reward_with_firius_tokens(user_id):
    """Atomically claim the old reward plus 10 cumulative Firius Tokens."""
    from data.balance import DAILY_QUEST_REWARD_ITEM_ID, DAILY_QUEST_REWARD_QUANTITY

    db = _db()
    db.reset_daily_quest_if_needed(user_id)
    conn = db.conn
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT progress, target_count, completed, reward_claimed
            FROM user_daily_quests WHERE user_id=?
            """,
            (int(user_id),),
        ).fetchone()
        if not row:
            conn.rollback()
            return {"success": False, "message": "❌ Щоденне завдання не знайдено."}
        progress, target_count, completed, reward_claimed = row
        if not bool(completed):
            conn.rollback()
            return {
                "success": False,
                "message": (
                    "❌ Щоденне завдання ще не виконано.\\n\\n"
                    f"📈 Прогрес: {int(progress or 0)}/{int(target_count or 0)}"
                ),
            }
        if bool(reward_claimed):
            conn.rollback()
            return {"success": False, "message": "✅ Нагороду за сьогодні вже отримано."}

        base_plan = _plan_stack_addition(
            conn, user_id, DAILY_QUEST_REWARD_ITEM_ID, DAILY_QUEST_REWARD_QUANTITY
        )
        token_plan = _plan_stack_addition(
            conn, user_id, FIRIUS_TOKEN_ITEM_ID, FIRIUS_TOKENS_PER_DAILY_REWARD
        )
        bag_row = conn.execute(
            "SELECT bag_slots FROM users WHERE user_id=?", (int(user_id),)
        ).fetchone()
        used_slots = int(conn.execute(
            "SELECT COUNT(*) FROM inventory WHERE user_id=?", (int(user_id),)
        ).fetchone()[0] or 0)
        capacity = int((bag_row[0] if bag_row else 0) or 0)
        required_slots = base_plan["new_slots"] + token_plan["new_slots"]
        if used_slots + required_slots > capacity:
            conn.rollback()
            return {
                "success": False,
                "code": "bag_full",
                "message": (
                    "🎒 Сумка переповнена.\\n\\n"
                    "Звільни місце в інвентарі та спробуй забрати нагороду ще раз.\\n"
                    "Нічого не було втрачено або частково нараховано."
                ),
            }

        _apply_stack_plan(conn, user_id, base_plan)
        _apply_stack_plan(conn, user_id, token_plan)
        updated = conn.execute(
            "UPDATE user_daily_quests SET reward_claimed=1 "
            "WHERE user_id=? AND completed=1 AND reward_claimed=0",
            (int(user_id),),
        ).rowcount
        if updated != 1:
            raise RuntimeError("Daily reward state changed during claim")
        conn.commit()
        return {
            "success": True,
            "base_item_id": base_plan["item_id"],
            "base_quantity": base_plan["quantity"],
            "firius_token_item_id": FIRIUS_TOKEN_ITEM_ID,
            "firius_token_quantity": FIRIUS_TOKENS_PER_DAILY_REWARD,
            "message": (
                "🎁 Ви отримали нагороду за щоденне завдання!\\n\\n"
                f"📦 {base_plan['name']} ×{base_plan['quantity']}\\n"
                f"🪙 {token_plan['name']} ×{token_plan['quantity']}\\n\\n"
                "Жетони Фіріуса накопичуються та не зникають наступного дня."
            ),
        }
    except Exception:
        conn.rollback()
        raise
'''

DB_APPEND = r'''

# ==============================
# ROM 10.3.0 DAILY QUEST FIRIUS TOKEN REWARD FACADE
# ==============================

def claim_daily_quest_reward(user_id):
    from systems.rune_system import claim_daily_quest_reward_with_firius_tokens as _func
    return _func(user_id)
'''

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_USER_ID = -100300001


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def quantity(conn, user_id, item_id):
    return int(conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) FROM inventory WHERE user_id=? AND item_id=?",
        (user_id, item_id),
    ).fetchone()[0] or 0)


def cleanup(db):
    for table in ("inventory_runes", "equipment_slots", "inventory", "user_daily_quests"):
        try:
            db.conn.execute(f"DELETE FROM {table} WHERE user_id=?" if table != "inventory_runes" else
                            "DELETE FROM inventory_runes WHERE inventory_id IN "
                            "(SELECT id FROM inventory WHERE user_id=?)", (FIXTURE_USER_ID,))
        except Exception:
            pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (FIXTURE_USER_ID,))
    db.conn.commit()


def prepare_completed(db):
    db.init_daily_quest_system()
    db.conn.execute(
        "UPDATE user_daily_quests SET progress=target_count, completed=1, reward_claimed=0 "
        "WHERE user_id=?", (FIXTURE_USER_ID,)
    )
    db.conn.commit()


def main():
    import db
    from data.balance import DAILY_QUEST_REWARD_ITEM_ID, DAILY_QUEST_REWARD_QUANTITY
    from data.runes import FIRIUS_TOKEN_ITEM_ID, FIRIUS_TOKENS_PER_DAILY_REWARD

    cleanup(db)
    try:
        db.create_user(FIXTURE_USER_ID)
        db.init_rune_system()
        db.reset_daily_quest_if_needed(FIXTURE_USER_ID)
        prepare_completed(db)

        base_before = quantity(db.conn, FIXTURE_USER_ID, DAILY_QUEST_REWARD_ITEM_ID)
        token_before = quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID)
        first = db.claim_daily_quest_reward(FIXTURE_USER_ID)
        if first.get("success") is not True:
            fail(f"first claim failed: {first}")
        if quantity(db.conn, FIXTURE_USER_ID, DAILY_QUEST_REWARD_ITEM_ID) - base_before != DAILY_QUEST_REWARD_QUANTITY:
            fail("base reward quantity mismatch")
        if quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID) - token_before != FIRIUS_TOKENS_PER_DAILY_REWARD:
            fail("Firius token reward quantity mismatch")
        if "Жетон Фіріуса" not in first.get("message", "") or "×10" not in first.get("message", ""):
            fail(f"success message missing token reward: {first}")

        second = db.claim_daily_quest_reward(FIXTURE_USER_ID)
        if second.get("success") is not False:
            fail("repeat claim unexpectedly succeeded")
        if quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID) != token_before + 10:
            fail("repeat claim changed token quantity")

        # Simulate the next day by creating a fresh claimable daily row.
        db.conn.execute(
            "UPDATE user_daily_quests SET quest_date='2000-01-01' WHERE user_id=?",
            (FIXTURE_USER_ID,),
        )
        db.conn.commit()
        db.reset_daily_quest_if_needed(FIXTURE_USER_ID)
        prepare_completed(db)
        third = db.claim_daily_quest_reward(FIXTURE_USER_ID)
        if third.get("success") is not True:
            fail(f"next-day claim failed: {third}")
        if quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID) != token_before + 20:
            fail("tokens did not accumulate across daily claims")

        # Full-bag contract: both rewards must remain unchanged and unclaimed.
        db.conn.execute(
            "UPDATE user_daily_quests SET quest_date='2000-01-01' WHERE user_id=?",
            (FIXTURE_USER_ID,),
        )
        db.conn.commit()
        db.reset_daily_quest_if_needed(FIXTURE_USER_ID)
        prepare_completed(db)
        # Existing reward stacks still had free capacity, so merely setting
        # bag_slots=used_slots would correctly allow the claim. Fill both
        # reward stacks to max_stack first, forcing the claim to require two
        # genuinely new inventory slots.
        for item_id in (DAILY_QUEST_REWARD_ITEM_ID, FIRIUS_TOKEN_ITEM_ID):
            max_stack = int(db.conn.execute(
                "SELECT max_stack FROM items WHERE id=?", (item_id,)
            ).fetchone()[0] or 1)
            row = db.conn.execute(
                "SELECT id FROM inventory WHERE user_id=? AND item_id=? ORDER BY id LIMIT 1",
                (FIXTURE_USER_ID, item_id),
            ).fetchone()
            if row:
                db.conn.execute(
                    "UPDATE inventory SET quantity=? WHERE id=?",
                    (max_stack, int(row[0])),
                )
            else:
                db.conn.execute(
                    "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
                    (FIXTURE_USER_ID, item_id, max_stack),
                )
        used = int(db.conn.execute(
            "SELECT COUNT(*) FROM inventory WHERE user_id=?", (FIXTURE_USER_ID,)
        ).fetchone()[0])
        db.conn.execute("UPDATE users SET bag_slots=? WHERE user_id=?", (used, FIXTURE_USER_ID))
        db.conn.commit()
        base_full_before = quantity(db.conn, FIXTURE_USER_ID, DAILY_QUEST_REWARD_ITEM_ID)
        token_full_before = quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID)
        full = db.claim_daily_quest_reward(FIXTURE_USER_ID)
        claimed = int(db.conn.execute(
            "SELECT reward_claimed FROM user_daily_quests WHERE user_id=?", (FIXTURE_USER_ID,)
        ).fetchone()[0])
        if full.get("code") != "bag_full" or claimed != 0:
            fail(f"full-bag claim contract failed: {full}, claimed={claimed}")
        if quantity(db.conn, FIXTURE_USER_ID, DAILY_QUEST_REWARD_ITEM_ID) != base_full_before:
            fail("full-bag failure partially changed base reward")
        if quantity(db.conn, FIXTURE_USER_ID, FIRIUS_TOKEN_ITEM_ID) != token_full_before:
            fail("full-bag failure partially changed tokens")

        print("[OK] Daily Quest Firius Token reward contracts")
        print("- base reward preserved: 3 small HP potions")
        print("- Firius Tokens per successful claim: 10")
        print("- repeat claim token duplication: 0")
        print("- tokens accumulate across daily resets: yes")
        print("- full-bag partial reward: 0")
        print("- reward_claimed on failed claim: 0")
        print("- isolated fixture cleanup: pending")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
'''


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if all((root / rel).is_file() for rel in (SYSTEM_REL, DB_REL, HANDLER_REL)) and (root / "game.db").is_file():
            return root
    fail("Не знайдено ROM із застосованим 10.2.0.")


def update_system(source):
    marker = "ROM 10.3.0 DAILY QUEST FIRIUS TOKEN REWARD"
    return source if marker in source else source.rstrip() + SYSTEM_APPEND + "\n"


def update_db(source):
    marker = "ROM 10.3.0 DAILY QUEST FIRIUS TOKEN REWARD FACADE"
    return source if marker in source else source.rstrip() + DB_APPEND + "\n"


def update_handler(source):
    if "🪙 Жетон Фіріуса ×10" in source:
        return source
    old = '        "🔴 Мале зілля здоров’я ×3\\n"\n'
    new = (
        '        "🔴 Мале зілля здоров’я ×3\\n"\n'
        '        "🪙 Жетон Фіріуса ×10\\n"\n'
        '        "ℹ️ Жетони накопичуються та не зникають наступного дня.\\n"\n'
    )
    if old not in source:
        raise RuntimeError("handlers/daily.py reward text anchor not found")
    updated = source.replace(old, new, 1)
    ast.parse(updated, filename="handlers/daily.py")
    return updated


def run(root, rel, env):
    result = subprocess.run([sys.executable, str(root / rel)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{rel} exit code {result.returncode}")


def main():
    root = find_root()
    originals = {
        SYSTEM_REL: (root / SYSTEM_REL).read_text(encoding="utf-8-sig"),
        DB_REL: (root / DB_REL).read_text(encoding="utf-8-sig"),
        HANDLER_REL: (root / HANDLER_REL).read_text(encoding="utf-8-sig"),
    }
    updates = {
        SYSTEM_REL: update_system(originals[SYSTEM_REL]),
        DB_REL: update_db(originals[DB_REL]),
        HANDLER_REL: update_handler(originals[HANDLER_REL]),
        TEST_REL: TEST_SOURCE,
    }

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = {}
    for rel in updates:
        path = root / rel
        if path.exists():
            backup = backup_dir / f"{str(rel).replace('/', '_').replace(chr(92), '_')}_{PATCH_ID}_{stamp}.bak"
            shutil.copy2(path, backup)
            backups[rel] = backup
    db_backup = backup_dir / f"game.db_{PATCH_ID}_{stamp}.bak"
    shutil.copy2(root / "game.db", db_backup)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        for rel, content in updates.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            py_compile.compile(str(path), doraise=True)

        checks = [
            TEST_REL,
            Path("tools/smoke_test_rune_data_model.py"),
            Path("tools/smoke_test_inventory_refine_contracts.py"),
            Path("tools/smoke_test_player_combat_stats.py"),
            Path("tools/smoke_test_rom_core.py"),
            Path("tools/check_imports.py"),
        ]
        for rel in checks:
            if not (root / rel).is_file():
                raise RuntimeError(f"missing check: {rel}")
            run(root, rel, env)

        conn = sqlite3.connect(root / "game.db")
        try:
            residue = sum(
                int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id=-100300001").fetchone()[0])
                for table in ("users", "inventory", "equipment_slots", "user_daily_quests")
            )
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            conn.close()
        if residue != 0 or quick != "ok":
            raise RuntimeError(f"final DB contract failed: residue={residue}, quick={quick}")
    except Exception as exc:
        shutil.copy2(db_backup, root / "game.db")
        for rel in updates:
            path = root / rel
            if rel in backups:
                shutil.copy2(backups[rel], path)
            elif path.exists():
                path.unlink()
        fail(f"Перевірка не пройдена; код і game.db відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Щоденне завдання видає 10 Жетонів Фіріуса разом із попередньою нагородою.")
    print("✅ Жетони накопичуються між днями та не мають daily reset.")
    print("✅ Повторне отримання нагороди не дублює жетони.")
    print("✅ При переповненій сумці нагорода не нараховується частково.")
    print("✅ Оновлено текст нагороди в меню щоденного завдання.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    for backup in backups.values():
        print(f"   {backup.relative_to(root)}")
    print("Перевірки:")
    print("   python ./tools/smoke_test_daily_firius_token_reward.py")
    print("   python ./tools/smoke_test_rune_data_model.py")
    print("   python ./tools/smoke_test_inventory_refine_contracts.py")
    print("   python ./tools/smoke_test_player_combat_stats.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")


if __name__ == "__main__":
    main()
