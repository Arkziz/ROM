# ROM 17.14.1.2 LEVEL UP REWARD BALANCE EXPANSION

# ROM 17.14.1 LEVEL UP REWARDS

"""Persistent and recoverable rewards for newly reached character levels."""

from __future__ import annotations



from datetime import datetime



from data.balance import REFINE_STONE_ITEM_ID



SMALL_HEALTH_POTION_ITEM_ID = 401

SMALL_MANA_POTION_ITEM_ID = 402

MEDIUM_HEALTH_POTION_ITEM_ID = 403

MEDIUM_MANA_POTION_ITEM_ID = 404

CRYSTAL_REWARD_ENABLED = False

# Stage 20.4.2b: approved deterministic level-up gold matrix. Each reached
# level uses 10% of expected same-level normal-mob combat income from the
# preceding source level, rounded to two decimals during the audit. Keeping
# this table frozen prevents reward drift when unrelated mob data changes.
LEVEL_UP_GOLD_BY_REACHED_LEVEL = {
    2: 0.45,
    3: 1.43,
    4: 4.30,
    5: 11.98,
    6: 34.40,
    7: 69.58,
    8: 130.73,
    9: 255.74,
    10: 479.19,
    11: 881.25,
}






def calculate_level_reward(reached_level):

    level = int(reached_level)

    if level not in LEVEL_UP_GOLD_BY_REACHED_LEVEL:
        raise ValueError(
            f"Level-up gold is not configured for reached level {level}. "
            "Add an audited combat-income matrix before enabling this level."
        )

    milestone = level % 5 == 0

    return {

        "reached_level": level,

        "gold": LEVEL_UP_GOLD_BY_REACHED_LEVEL[level],

        "small_health_potions": 3,

        "small_mana_potions": 1,

        "refine_stones": 4 if milestone else 2,

        "medium_health_potions": 2 if milestone else 0,

        "medium_mana_potions": 1 if milestone else 0,

        "crystals": 0,

        "milestone": milestone,

    }





def calculate_level_rewards(old_level, new_level):

    old_level = int(old_level)

    new_level = int(new_level)

    levels = list(range(old_level + 1, new_level + 1)) if new_level > old_level else []

    rows = [calculate_level_reward(level) for level in levels]

    return {

        "old_level": old_level,

        "new_level": new_level,

        "reached_levels": levels,

        "milestone_levels": [row["reached_level"] for row in rows if row["milestone"]],

        "gold": sum(row["gold"] for row in rows),

        "small_health_potions": sum(row["small_health_potions"] for row in rows),

        "small_mana_potions": sum(row["small_mana_potions"] for row in rows),

        "refine_stones": sum(row["refine_stones"] for row in rows),

        "medium_health_potions": sum(row["medium_health_potions"] for row in rows),

        "medium_mana_potions": sum(row["medium_mana_potions"] for row in rows),

        "crystals": 0,

        "rows": rows,

    }





def _table_columns(db, table_name):

    return {str(row[1]) for row in db.cursor.execute(f"PRAGMA table_info({table_name})").fetchall()}





def init_level_up_reward_system(db):

    db.cursor.execute("""

        CREATE TABLE IF NOT EXISTS level_up_rewards (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            reached_level INTEGER NOT NULL,

            gold_amount REAL NOT NULL DEFAULT 0,

            health_potion_quantity INTEGER NOT NULL DEFAULT 0,

            simple_extractor_quantity INTEGER NOT NULL DEFAULT 0,

            crystal_quantity INTEGER NOT NULL DEFAULT 0,

            gold_claimed INTEGER NOT NULL DEFAULT 0,

            items_claimed INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL,

            items_claimed_at TEXT,

            small_mana_potion_quantity INTEGER NOT NULL DEFAULT 0,

            refine_stone_quantity INTEGER NOT NULL DEFAULT 0,

            medium_health_potion_quantity INTEGER NOT NULL DEFAULT 0,

            medium_mana_potion_quantity INTEGER NOT NULL DEFAULT 0,

            UNIQUE(user_id, reached_level)

        )

    """)

    columns = _table_columns(db, "level_up_rewards")

    additions = {

        "small_mana_potion_quantity": "INTEGER NOT NULL DEFAULT 0",

        "refine_stone_quantity": "INTEGER NOT NULL DEFAULT 0",

        "medium_health_potion_quantity": "INTEGER NOT NULL DEFAULT 0",

        "medium_mana_potion_quantity": "INTEGER NOT NULL DEFAULT 0",

    }

    for name, declaration in additions.items():

        if name not in columns:

            db.cursor.execute(f"ALTER TABLE level_up_rewards ADD COLUMN {name} {declaration}")



    # Pending historical rows adopt the new item balance. Claimed rows stay untouched.

    db.cursor.execute("""

        UPDATE level_up_rewards

           SET health_potion_quantity=3,

               simple_extractor_quantity=0,

               small_mana_potion_quantity=1,

               refine_stone_quantity=5,

               medium_health_potion_quantity=CASE WHEN reached_level % 5=0 THEN 2 ELSE 0 END,

               medium_mana_potion_quantity=CASE WHEN reached_level % 5=0 THEN 1 ELSE 0 END

         WHERE items_claimed=0

    """)

    db.conn.commit()





def _insert_new_reward_rows(db, user_id, reward_plan):

    inserted_gold = 0.0

    inserted_levels = []

    now = datetime.now().isoformat()

    for row in reward_plan["rows"]:

        db.cursor.execute(

            """INSERT OR IGNORE INTO level_up_rewards (

                   user_id, reached_level, gold_amount,

                   health_potion_quantity, simple_extractor_quantity,

                   crystal_quantity, gold_claimed, items_claimed, created_at,

                   small_mana_potion_quantity, refine_stone_quantity,

                   medium_health_potion_quantity, medium_mana_potion_quantity

               ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, ?, ?, ?, ?, ?)""",

            (

                int(user_id), row["reached_level"], row["gold"],

                row["small_health_potions"], now,

                row["small_mana_potions"], row["refine_stones"],

                row["medium_health_potions"], row["medium_mana_potions"],

            ),

        )

        if db.cursor.rowcount == 1:

            inserted_gold += float(row["gold"])

            inserted_levels.append(int(row["reached_level"]))

    if inserted_gold:

        db.cursor.execute(

            "UPDATE users SET gold=COALESCE(gold, 0)+? WHERE user_id=?",

            (inserted_gold, int(user_id)),

        )

        placeholders = ",".join("?" for _ in inserted_levels)

        db.cursor.execute(

            f"UPDATE level_up_rewards SET gold_claimed=1 WHERE user_id=? AND reached_level IN ({placeholders})",

            (int(user_id), *inserted_levels),

        )

    return inserted_gold, inserted_levels





def _pending_item_totals(db, user_id):

    row = db.cursor.execute(

        """SELECT COALESCE(SUM(health_potion_quantity),0),

                  COALESCE(SUM(small_mana_potion_quantity),0),

                  COALESCE(SUM(refine_stone_quantity),0),

                  COALESCE(SUM(medium_health_potion_quantity),0),

                  COALESCE(SUM(medium_mana_potion_quantity),0)

             FROM level_up_rewards

            WHERE user_id=? AND items_claimed=0""",

        (int(user_id),),

    ).fetchone()

    values = list(row or (0, 0, 0, 0, 0))

    return tuple(int(value or 0) for value in values)





def try_claim_pending_items(db, user_id):

    from db_modules.inventory import add_item



    small_hp, small_mp, stones, medium_hp, medium_mp = _pending_item_totals(db, user_id)

    quantities = (

        (SMALL_HEALTH_POTION_ITEM_ID, small_hp),

        (SMALL_MANA_POTION_ITEM_ID, small_mp),

        (REFINE_STONE_ITEM_ID, stones),

        (MEDIUM_HEALTH_POTION_ITEM_ID, medium_hp),

        (MEDIUM_MANA_POTION_ITEM_ID, medium_mp),

    )

    if not any(quantity > 0 for _item_id, quantity in quantities):

        return {"success": True, "pending": False}



    savepoint = "rom_level_up_reward_items_17_14_1_2"

    db.cursor.execute(f"SAVEPOINT {savepoint}")

    try:

        for item_id, quantity in quantities:

            if quantity <= 0:

                continue

            result = add_item(user_id, item_id, quantity, commit=False)

            if not result.get("success"):

                raise RuntimeError(result.get("message") or f"item {item_id} delivery failed")

        db.cursor.execute(

            """UPDATE level_up_rewards

                  SET items_claimed=1, items_claimed_at=?

                WHERE user_id=? AND items_claimed=0""",

            (datetime.now().isoformat(), int(user_id)),

        )

        db.cursor.execute(f"RELEASE {savepoint}")

        return {

            "success": True, "pending": False,

            "small_health_potions": small_hp, "small_mana_potions": small_mp,

            "refine_stones": stones, "medium_health_potions": medium_hp,

            "medium_mana_potions": medium_mp,

        }

    except Exception as error:

        db.cursor.execute(f"ROLLBACK TO {savepoint}")

        db.cursor.execute(f"RELEASE {savepoint}")

        return {"success": False, "pending": True, "message": str(error)}





def apply_level_up_rewards_in_transaction(db, user_id, old_level, new_level):

    plan = calculate_level_rewards(old_level, new_level)

    gold, inserted_levels = _insert_new_reward_rows(db, user_id, plan)

    item_result = try_claim_pending_items(db, user_id)

    return {**plan, "gold_awarded_now": gold, "new_ledger_levels": inserted_levels, "item_result": item_result}





def build_level_up_reward_message(result):

    levels = result.get("new_ledger_levels") or []

    if not levels:

        return ""

    title = f"🎉 Новий рівень: {levels[0]}" if len(levels) == 1 else f"🎉 Отримано рівні: {levels[0]}–{levels[-1]}"

    rows = [row for row in result.get("rows", []) if row.get("reached_level") in levels]

    total = lambda key: sum(int(row.get(key, 0)) for row in rows)

    lines = [

        title, "", "🎁 Нагорода:",

        f"• Золото: {float(result.get('gold_awarded_now', 0) or 0):.2f}",

        f"• Мале зілля здоров’я ×{total('small_health_potions')}",

        f"• Мале зілля мани ×{total('small_mana_potions')}",

        f"• Камінь посилення ×{total('refine_stones')}",

    ]

    if total("medium_health_potions"):

        lines.append(f"• Середнє зілля здоров’я ×{total('medium_health_potions')}")

    if total("medium_mana_potions"):

        lines.append(f"• Середнє зілля мани ×{total('medium_mana_potions')}")

    if result.get("item_result", {}).get("pending"):

        lines.extend(["", "🎒 Предметна нагорода очікує вільного місця в сумці."])

    attribute_points_awarded = int(result.get("attribute_points_awarded", 0) or 0)
    if attribute_points_awarded > 0:
        free_attribute_points = int(result.get("free_attribute_points", 0) or 0)
        lines.extend([
            "",
            f"⭐ Отримано очок характеристик: {attribute_points_awarded}",
            f"📌 Вільних очок загалом: {free_attribute_points}",
            "",
            "Розподілити очки можна у профілі: «Характеристики».",
        ])
    return "\n".join(lines)

