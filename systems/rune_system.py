"""Rune System foundation: schema, seed, reads and fusion-selection validation."""
from __future__ import annotations

from data.runes import (
    ALL_RUNE_SYSTEM_ITEM_DEFINITIONS,
    FIRIUS_TOKEN_ITEM_ID,
    FIRIUS_TOKENS_PER_DAILY_REWARD,
    PERFECT_RUNE_EXTRACTOR_ITEM_ID,
    RUNE_EXTRACTOR_ITEM_ID,
    RUNE_FUSION_SOURCE_QUANTITY,
    RUNE_FUSION_TOKEN_QUANTITY,
    RUNE_ITEM_DEFINITIONS,
    RUNE_SLOT_LIMITS,
    get_rune_definition,
    get_rune_item_id,
    get_rune_slot_limit,
    is_rune_item_id,
)


def _db():
    import db
    return db


def init_rune_system():
    """Create the normalized socket table and seed all 28 system items."""
    db = _db()
    conn = db.conn
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_runes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inventory_id INTEGER NOT NULL,
            slot_index INTEGER NOT NULL CHECK(slot_index >= 0),
            rune_item_id INTEGER NOT NULL,
            rune_stat TEXT NOT NULL CHECK(rune_stat IN ('STR','STA','DEX','INT','WIS')),
            rune_level INTEGER NOT NULL CHECK(rune_level BETWEEN 1 AND 5),
            inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(inventory_id, slot_index),
            FOREIGN KEY(inventory_id) REFERENCES inventory(id) ON DELETE CASCADE,
            FOREIGN KEY(rune_item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_inventory_id "
        "ON inventory_runes(inventory_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_runes_rune_item_id "
        "ON inventory_runes(rune_item_id)"
    )
    seeded = seed_rune_system_items(commit=False)
    conn.commit()
    return {"success": True, "table": "inventory_runes", "seeded": seeded}


def _item_columns():
    db = _db()
    return {row[1] for row in db.conn.execute("PRAGMA table_info(items)").fetchall()}


def _seed_values(definition):
    values = {
        "id": definition["id"],
        "name": definition["name"],
        "type": definition["type"],
        "rarity": definition["rarity"],
        "category": definition["category"],
        "slot_key": "",
        "weapon_hands": 1,
        "max_stack": definition["max_stack"],
        "sell_price": definition["sell_price"],
        "bonus_str": 0,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "pdef": 0,
        "mdef": 0,
        "item_level": 1,
        "is_generated": 0,
        "item_subtype": "",
        "armor_type": "",
        "weapon_min_damage": 0,
        "weapon_max_damage": 0,
        "weapon_min_magic_damage": 0,
        "weapon_max_magic_damage": 0,
        "weapon_attack_type": "",
        "shop_preview_owner": None,
        "shop_preview_price": 0,
    }
    return values


def seed_rune_system_items(commit=True):
    """Idempotent seed that refuses semantic ID/type collisions."""
    db = _db()
    columns = _item_columns()
    seeded = 0
    for item_id, definition in ALL_RUNE_SYSTEM_ITEM_DEFINITIONS.items():
        existing = db.conn.execute(
            "SELECT name, type FROM items WHERE id=?", (item_id,)
        ).fetchone()
        if existing and str(existing[1]) != definition["type"]:
            raise RuntimeError(
                f"Rune item ID collision {item_id}: existing={existing}, "
                f"expected_type={definition['type']}"
            )
        values = _seed_values(definition)
        selected = [name for name in values if name in columns]
        placeholders = ", ".join("?" for _ in selected)
        column_sql = ", ".join(selected)
        update_sql = ", ".join(
            f"{name}=excluded.{name}" for name in selected if name != "id"
        )
        db.conn.execute(
            f"INSERT INTO items ({column_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {update_sql}",
            tuple(values[name] for name in selected),
        )
        seeded += 1
    if commit:
        db.conn.commit()
    return seeded


def get_inventory_runes(inventory_id):
    db = _db()
    rows = db.conn.execute(
        """
        SELECT id, inventory_id, slot_index, rune_item_id,
               rune_stat, rune_level, inserted_at
        FROM inventory_runes
        WHERE inventory_id=?
        ORDER BY slot_index, id
        """,
        (int(inventory_id),),
    ).fetchall()
    return [
        {
            "id": row[0], "inventory_id": row[1], "slot_index": row[2],
            "rune_item_id": row[3], "stat": row[4], "level": row[5],
            "bonus": row[5], "inserted_at": row[6],
        }
        for row in rows
    ]


def get_inventory_rune_capacity(inventory_id):
    db = _db()
    row = db.conn.execute(
        """
        SELECT items.slot_key
        FROM inventory JOIN items ON items.id=inventory.item_id
        WHERE inventory.id=?
        """,
        (int(inventory_id),),
    ).fetchone()
    return get_rune_slot_limit(row[0] if row else "")


def get_inventory_rune_socket_summary(inventory_id):
    runes = get_inventory_runes(inventory_id)
    capacity = get_inventory_rune_capacity(inventory_id)
    return {
        "inventory_id": int(inventory_id),
        "used": len(runes),
        "capacity": capacity,
        "free": max(0, capacity - len(runes)),
        "runes": runes,
    }


def get_equipped_rune_stat_totals(user_id):
    """Read API prepared for 10.7.0. No stat integration is active yet."""
    db = _db()
    totals = {"str": 0, "sta": 0, "dex": 0, "int": 0, "wis": 0}
    rows = db.conn.execute(
        """
        SELECT ir.rune_stat, ir.rune_level
        FROM equipment_slots es
        JOIN inventory i ON i.id=es.inventory_id AND i.user_id=es.user_id
        JOIN inventory_runes ir ON ir.inventory_id=i.id
        WHERE es.user_id=? AND COALESCE(i.durability, 100) > 0
        """,
        (int(user_id),),
    ).fetchall()
    for stat, level in rows:
        key = str(stat).lower()
        if key in totals:
            totals[key] += int(level or 0)
    return totals


def validate_rune_fusion_selection(rune_item_ids):
    """Validate the future 3-rune recipe and return a user-facing reason."""
    try:
        selected = [int(item_id) for item_id in rune_item_ids]
    except Exception:
        selected = []
    if len(selected) != RUNE_FUSION_SOURCE_QUANTITY:
        return {
            "success": False,
            "code": "wrong_quantity",
            "message": "❌ Для переробки потрібно вибрати рівно 3 однакові руни.",
        }
    definitions = [get_rune_definition(item_id) for item_id in selected]
    if any(definition is None for definition in definitions):
        return {
            "success": False,
            "code": "not_rune",
            "message": "❌ Для переробки можна використовувати лише руни характеристик.",
        }
    keys = {(definition["stat"], definition["level"]) for definition in definitions}
    if len(keys) != 1:
        return {
            "success": False,
            "code": "different_runes",
            "message": "❌ Потрібно вибрати 3 однакові руни одного типу й рівня.",
        }
    definition = definitions[0]
    if definition["level"] >= 5:
        return {
            "success": False,
            "code": "max_level",
            "message": "❌ Руна V вже має максимальний рівень і не переробляється.",
        }
    result_item_id = get_rune_item_id(definition["stat"], definition["level"] + 1)
    return {
        "success": True,
        "code": "ok",
        "message": "✅ Руни підходять для переробки.",
        "source_item_id": definition["id"],
        "result_item_id": result_item_id,
        "source_quantity": RUNE_FUSION_SOURCE_QUANTITY,
        "token_item_id": FIRIUS_TOKEN_ITEM_ID,
        "token_quantity": RUNE_FUSION_TOKEN_QUANTITY,
    }

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
                    "❌ Щоденне завдання ще не виконано.\n\n"
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
                    "🎒 Сумка переповнена.\n\n"
                    "Звільни місце в інвентарі та спробуй забрати нагороду ще раз.\n"
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
                "🎁 Ви отримали нагороду за щоденне завдання!\n\n"
                f"📦 {base_plan['name']} ×{base_plan['quantity']}\n"
                f"🪙 {token_plan['name']} ×{token_plan['quantity']}\n\n"
                "Жетони Фіріуса накопичуються та не зникають наступного дня."
            ),
        }
    except Exception:
        conn.rollback()
        raise

