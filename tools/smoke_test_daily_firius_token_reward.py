#!/usr/bin/env python3
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
