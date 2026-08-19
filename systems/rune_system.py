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

# ==============================
# ROM 10.5.0 EQUIPMENT RUNE SLOT CONTRACTS
# ==============================


def get_equipment_rune_slot_info(user_id, inventory_id):
    """Return ownership, equipment type, capacity and current socket state."""
    db = _db()
    try:
        inventory_id = int(inventory_id)
        user_id = int(user_id)
    except Exception:
        return {
            "success": False,
            "code": "invalid_id",
            "message": "❌ Некоректний предмет спорядження.",
        }

    row = db.conn.execute(
        """
        SELECT i.id, i.user_id, i.durability, it.name, it.category, it.slot_key
        FROM inventory i
        JOIN items it ON it.id=i.item_id
        WHERE i.id=?
        """,
        (inventory_id,),
    ).fetchone()
    if not row:
        return {
            "success": False,
            "code": "not_found",
            "message": "❌ Предмет не знайдено.",
        }
    if int(row[1]) != user_id:
        return {
            "success": False,
            "code": "not_owner",
            "message": "❌ Цей предмет не належить персонажу.",
        }

    category = str(row[4] or "")
    slot_key = str(row[5] or "")
    capacity = get_rune_slot_limit(slot_key)
    if category != "equipment" or capacity <= 0:
        return {
            "success": False,
            "code": "not_equipment",
            "message": "❌ Руни можна вставляти лише у спорядження з рунними слотами.",
        }

    runes = get_inventory_runes(inventory_id)
    occupied = {int(rune["slot_index"]) for rune in runes}
    slots = []
    for slot_index in range(capacity):
        rune = next(
            (item for item in runes if int(item["slot_index"]) == slot_index),
            None,
        )
        slots.append({
            "slot_index": slot_index,
            "display_number": slot_index + 1,
            "occupied": rune is not None,
            "rune": rune,
        })

    return {
        "success": True,
        "inventory_id": inventory_id,
        "name": str(row[3]),
        "slot_key": slot_key,
        "durability": int(row[2] if row[2] is not None else 100),
        "capacity": capacity,
        "used": len(occupied),
        "free": max(0, capacity - len(occupied)),
        "slots": slots,
    }


def get_user_rune_slot_equipment(user_id):
    """List owned equipment that supports rune sockets."""
    db = _db()
    rows = db.conn.execute(
        """
        SELECT i.id
        FROM inventory i
        JOIN items it ON it.id=i.item_id
        WHERE i.user_id=? AND it.category='equipment'
        ORDER BY i.id
        """,
        (int(user_id),),
    ).fetchall()
    result = []
    for (inventory_id,) in rows:
        info = get_equipment_rune_slot_info(user_id, inventory_id)
        if info.get("success"):
            result.append(info)
    return result


def format_equipment_rune_slots_text(user_id, inventory_id):
    """Build the read-only socket block shown in equipment details."""
    info = get_equipment_rune_slot_info(user_id, inventory_id)
    if not info.get("success"):
        return ""

    from data.runes import RUNE_LEVEL_ROMAN, RUNE_STAT_NAMES

    lines = [
        "",
        "💠 Рунні слоти:",
        f"• Використано: {info['used']}/{info['capacity']}",
    ]
    for slot in info["slots"]:
        if not slot["occupied"]:
            lines.append(f"• Слот {slot['display_number']}: порожній")
            continue
        rune = slot["rune"]
        stat_name = RUNE_STAT_NAMES.get(rune["stat"], rune["stat"])
        roman = RUNE_LEVEL_ROMAN.get(int(rune["level"]), str(rune["level"]))
        lines.append(
            f"• Слот {slot['display_number']}: Руна {stat_name} {roman} "
            f"(+{int(rune['bonus'])})"
        )
    lines.append("")
    return "\n".join(lines)

# ==============================
# ROM 10.6.0 ATOMIC RUNE INSERTION
# ==============================


def get_user_inventory_rune_stacks(user_id):
    """Return owned canonical rune stacks eligible for Rune Master selection."""
    db = _db()
    rows = db.conn.execute(
        """
        SELECT i.id, i.item_id, i.quantity, it.name
        FROM inventory i
        JOIN items it ON it.id=i.item_id
        WHERE i.user_id=? AND i.quantity > 0 AND it.category='rune'
        ORDER BY i.item_id, i.id
        """,
        (int(user_id),),
    ).fetchall()
    result = []
    for inventory_id, item_id, quantity, name in rows:
        definition = get_rune_definition(item_id)
        if definition is None:
            continue
        result.append({
            "inventory_id": int(inventory_id),
            "item_id": int(item_id),
            "quantity": int(quantity),
            "name": str(name),
            "stat": definition["stat"],
            "level": int(definition["level"]),
            "bonus": int(definition["bonus"]),
        })
    return result


def get_rune_insertion_preview(user_id, equipment_inventory_id, slot_index, rune_inventory_id):
    """Validate current state without mutation and build confirmation metadata."""
    db = _db()
    equipment = get_equipment_rune_slot_info(user_id, equipment_inventory_id)
    if not equipment.get("success"):
        return equipment
    try:
        slot_index = int(slot_index)
        rune_inventory_id = int(rune_inventory_id)
    except Exception:
        return {
            "success": False,
            "code": "invalid_selection",
            "message": "❌ Некоректний вибір рунного слота або руни.",
        }
    if slot_index < 0 or slot_index >= int(equipment["capacity"]):
        return {
            "success": False,
            "code": "invalid_slot",
            "message": "❌ Обраний рунний слот не існує для цього предмета.",
        }
    if any(
        int(item["slot_index"]) == slot_index
        for item in get_inventory_runes(equipment_inventory_id)
    ):
        return {
            "success": False,
            "code": "slot_occupied",
            "message": "❌ Цей рунний слот уже зайнятий.",
        }
    row = db.conn.execute(
        """
        SELECT i.item_id, i.quantity, it.name, it.category
        FROM inventory i JOIN items it ON it.id=i.item_id
        WHERE i.id=? AND i.user_id=?
        """,
        (rune_inventory_id, int(user_id)),
    ).fetchone()
    if not row or int(row[1] or 0) <= 0:
        return {
            "success": False,
            "code": "rune_missing",
            "message": "❌ Обрана руна відсутня в інвентарі.",
        }
    definition = get_rune_definition(row[0])
    if definition is None or str(row[3]) != "rune":
        return {
            "success": False,
            "code": "not_rune",
            "message": "❌ Обраний предмет не є руною характеристики.",
        }
    return {
        "success": True,
        "equipment_inventory_id": int(equipment_inventory_id),
        "equipment_name": equipment["name"],
        "slot_index": slot_index,
        "slot_number": slot_index + 1,
        "capacity": equipment["capacity"],
        "rune_inventory_id": rune_inventory_id,
        "rune_item_id": int(row[0]),
        "rune_name": str(row[2]),
        "rune_quantity": int(row[1]),
        "stat": definition["stat"],
        "level": int(definition["level"]),
        "bonus": int(definition["bonus"]),
    }


def insert_rune_into_equipment(user_id, equipment_inventory_id, slot_index, rune_inventory_id):
    """Atomically consume one owned rune and occupy one empty equipment socket."""
    db = _db()
    conn = db.conn
    try:
        conn.execute("BEGIN IMMEDIATE")
        preview = get_rune_insertion_preview(
            user_id,
            equipment_inventory_id,
            slot_index,
            rune_inventory_id,
        )
        if not preview.get("success"):
            conn.rollback()
            return preview

        update = conn.execute(
            """
            UPDATE inventory
            SET quantity=quantity-1
            WHERE id=? AND user_id=? AND item_id=? AND quantity>0
            """,
            (
                preview["rune_inventory_id"],
                int(user_id),
                preview["rune_item_id"],
            ),
        )
        if update.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "code": "rune_missing",
                "message": "❌ Руна вже відсутня в інвентарі.",
            }
        conn.execute(
            "DELETE FROM inventory WHERE id=? AND user_id=? AND quantity<=0",
            (preview["rune_inventory_id"], int(user_id)),
        )
        try:
            conn.execute(
                """
                INSERT INTO inventory_runes
                    (inventory_id, slot_index, rune_item_id, rune_stat, rune_level)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    preview["equipment_inventory_id"],
                    preview["slot_index"],
                    preview["rune_item_id"],
                    preview["stat"],
                    preview["level"],
                ),
            )
        except Exception as error:
            conn.rollback()
            if "UNIQUE" in str(error).upper():
                return {
                    "success": False,
                    "code": "slot_occupied",
                    "message": "❌ Цей рунний слот уже зайнятий.",
                }
            raise
        conn.commit()
        return {
            **preview,
            "success": True,
            "code": "inserted",
            "message": (
                "✅ Руну успішно вставлено!\n\n"
                f"⚔️ Спорядження: {preview['equipment_name']}\n"
                f"💠 Слот {preview['slot_number']}/{preview['capacity']}: "
                f"{preview['rune_name']}\n"
                f"📈 Майбутній бонус: +{preview['bonus']} "
                f"до {__import__('data.runes', fromlist=['RUNE_STAT_NAMES']).RUNE_STAT_NAMES.get(preview['stat'], preview['stat'])}\n\n"
                "Бонус буде підключено до характеристик у наступному етапі."
            ),
        }
    except Exception:
        conn.rollback()
        raise

# ==============================
# ROM 10.7.0 POST-INSERT RESOURCE SYNC
# ==============================

_RUNE_STATS_BASE_INSERT_10_7_0 = insert_rune_into_equipment


def insert_rune_into_equipment(user_id, equipment_inventory_id, slot_index, rune_inventory_id):
    """Insert a rune, then clamp/sync HP and MP without free healing."""
    result = _RUNE_STATS_BASE_INSERT_10_7_0(
        user_id,
        equipment_inventory_id,
        slot_index,
        rune_inventory_id,
    )
    if not result.get("success"):
        return result
    db = _db()
    try:
        hp_sync = db.sync_user_max_hp(user_id, heal_to_full=False)
    except Exception:
        hp_sync = None
    try:
        db.refresh_user_mp(user_id)
        row = db.conn.execute(
            "SELECT mp, max_mp FROM users WHERE user_id=?", (int(user_id),)
        ).fetchone()
        mp_sync = {
            "mp": int(row[0] or 0) if row else 0,
            "max_mp": int(row[1] or 0) if row else 0,
        }
    except Exception:
        mp_sync = None
    result["hp_sync"] = hp_sync
    result["mp_sync"] = mp_sync
    result["message"] = result["message"].replace(
        "📈 Майбутній бонус:",
        "📈 Активний бонус після екіпірування:",
    ).replace(
        "Бонус буде підключено до характеристик у наступному етапі.",
        "Бонус діє, коли предмет екіпірований і має міцність більше 0.",
    )
    return result

# ==============================
# ROM 10.8.0 ATOMIC RUNE FUSION
# ==============================


def _inventory_item_total(conn, user_id, item_id):
    return int(conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM inventory "
        "WHERE user_id=? AND item_id=?",
        (int(user_id), int(item_id)),
    ).fetchone()[0] or 0)


def _consume_stack_quantity(conn, user_id, item_id, quantity):
    remaining = int(quantity)
    rows = conn.execute(
        "SELECT id, quantity FROM inventory "
        "WHERE user_id=? AND item_id=? ORDER BY id",
        (int(user_id), int(item_id)),
    ).fetchall()
    if sum(int(row[1] or 0) for row in rows) < remaining:
        return False
    for inventory_id, current in rows:
        current = int(current or 0)
        take = min(current, remaining)
        new_quantity = current - take
        if new_quantity > 0:
            conn.execute(
                "UPDATE inventory SET quantity=? WHERE id=? AND user_id=?",
                (new_quantity, int(inventory_id), int(user_id)),
            )
        else:
            conn.execute(
                "DELETE FROM inventory WHERE id=? AND user_id=?",
                (int(inventory_id), int(user_id)),
            )
        remaining -= take
        if remaining <= 0:
            break
    return remaining == 0


def _add_stack_quantity_in_transaction(conn, user_id, item_id, quantity):
    """Plan and apply a rune-system stack addition inside the caller transaction."""
    # ROM 17.4.1 RUNE TRANSACTIONAL STACK CAPACITY RECOVERY
    user_id = int(user_id)
    item_id = int(item_id)
    quantity = int(quantity)
    if quantity <= 0:
        return {"success": False, "code": "invalid_quantity"}

    item = conn.execute(
        "SELECT name, max_stack FROM items WHERE id=?", (item_id,)
    ).fetchone()
    if not item:
        return {"success": False, "code": "result_missing"}
    name, max_stack = str(item[0]), max(1, int(item[1] or 1))

    rows = conn.execute(
        "SELECT id, quantity FROM inventory "
        "WHERE user_id=? AND item_id=? ORDER BY id ASC",
        (user_id, item_id),
    ).fetchall()

    # Build the complete plan before any UPDATE/INSERT. This guarantees that a
    # failed capacity check leaves even the caller's open transaction untouched.
    remaining = quantity
    updates = []
    for inventory_id, current in rows:
        current = max(0, int(current or 0))
        add = min(max(0, max_stack - current), remaining)
        if add:
            updates.append((current + add, int(inventory_id)))
            remaining -= add
        if remaining <= 0:
            break

    required_new_rows = (
        (remaining + max_stack - 1) // max_stack if remaining > 0 else 0
    )
    used = int(conn.execute(
        "SELECT COUNT(*) FROM inventory WHERE user_id=?", (user_id,)
    ).fetchone()[0] or 0)
    user = conn.execute(
        "SELECT bag_slots FROM users WHERE user_id=?", (user_id,)
    ).fetchone()
    capacity = max(40, int((user[0] if user else 40) or 40))

    if used + required_new_rows > capacity:
        return {
            "success": False,
            "code": "bag_full",
            "name": name,
            "added": 0,
            "required_new_rows": required_new_rows,
            "used_slots": used,
            "capacity": capacity,
        }

    for new_quantity, inventory_id in updates:
        changed = conn.execute(
            "UPDATE inventory SET quantity=? WHERE id=? AND user_id=?",
            (new_quantity, inventory_id, user_id),
        ).rowcount
        if changed != 1:
            raise RuntimeError("Не вдалося оновити запланований стак руни.")

    inserted_ids = []
    while remaining > 0:
        add = min(max_stack, remaining)
        cursor = conn.execute(
            "INSERT INTO inventory (user_id,item_id,quantity) VALUES (?,?,?)",
            (user_id, item_id, add),
        )
        inserted_ids.append(int(cursor.lastrowid))
        remaining -= add

    return {
        "success": True,
        "name": name,
        "added": quantity,
        "required_new_rows": required_new_rows,
        "inserted_inventory_ids": inserted_ids,
        "used_slots": used + required_new_rows,
        "capacity": capacity,
    }



def get_available_rune_fusion_recipes(user_id):
    """Return only level I-IV rune stacks with at least three copies."""
    db = _db()
    rows = db.conn.execute(
        """
        SELECT i.item_id, SUM(i.quantity) AS total_quantity
        FROM inventory i JOIN items it ON it.id=i.item_id
        WHERE i.user_id=? AND it.category='rune'
        GROUP BY i.item_id
        HAVING SUM(i.quantity) >= ?
        ORDER BY i.item_id
        """,
        (int(user_id), RUNE_FUSION_SOURCE_QUANTITY),
    ).fetchall()
    recipes = []
    for item_id, quantity in rows:
        definition = get_rune_definition(item_id)
        if not definition or int(definition["level"]) >= 5:
            continue
        result_item_id = get_rune_item_id(
            definition["stat"], int(definition["level"]) + 1
        )
        result = get_rune_definition(result_item_id)
        recipes.append({
            "source_item_id": int(item_id),
            "source_name": definition["name"],
            "source_quantity_owned": int(quantity),
            "source_quantity_required": RUNE_FUSION_SOURCE_QUANTITY,
            "result_item_id": int(result_item_id),
            "result_name": result["name"],
            "token_item_id": FIRIUS_TOKEN_ITEM_ID,
            "token_quantity_required": RUNE_FUSION_TOKEN_QUANTITY,
            "stat": definition["stat"],
            "source_level": int(definition["level"]),
            "result_level": int(result["level"]),
        })
    return recipes


def get_firius_token_quantity(user_id):
    return _inventory_item_total(_db().conn, user_id, FIRIUS_TOKEN_ITEM_ID)


def get_rune_fusion_preview(user_id, source_item_id):
    definition = get_rune_definition(source_item_id)
    if not definition:
        return {
            "success": False, "code": "not_rune",
            "message": "❌ Для переробки можна використовувати лише руни характеристик.",
        }
    if int(definition["level"]) >= 5:
        return {
            "success": False, "code": "max_level",
            "message": "❌ Руна V уже має максимальний рівень і не переробляється.",
        }
    db = _db()
    rune_quantity = _inventory_item_total(db.conn, user_id, source_item_id)
    token_quantity = get_firius_token_quantity(user_id)
    if rune_quantity < RUNE_FUSION_SOURCE_QUANTITY:
        return {
            "success": False, "code": "not_enough_runes",
            "message": "❌ Потрібно 3 однакові руни одного типу й рівня.",
        }
    if token_quantity < RUNE_FUSION_TOKEN_QUANTITY:
        return {
            "success": False, "code": "not_enough_tokens",
            "message": "❌ Для переробки потрібен 1 Жетон Фіріуса.",
        }
    result_item_id = get_rune_item_id(
        definition["stat"], int(definition["level"]) + 1
    )
    result = get_rune_definition(result_item_id)
    return {
        "success": True,
        "source_item_id": int(source_item_id),
        "source_name": definition["name"],
        "source_quantity_owned": rune_quantity,
        "source_quantity_required": RUNE_FUSION_SOURCE_QUANTITY,
        "token_item_id": FIRIUS_TOKEN_ITEM_ID,
        "token_quantity_owned": token_quantity,
        "token_quantity_required": RUNE_FUSION_TOKEN_QUANTITY,
        "result_item_id": int(result_item_id),
        "result_name": result["name"],
        "result_quantity": 1,
        "success_chance": 100,
    }


def fuse_runes_with_firius_token(user_id, source_item_id):
    """Atomically consume 3 identical runes and 1 token, then add 1 next rune."""
    db = _db()
    conn = db.conn
    try:
        conn.execute("BEGIN IMMEDIATE")
        preview = get_rune_fusion_preview(user_id, source_item_id)
        if not preview.get("success"):
            conn.rollback()
            return preview
        if not _consume_stack_quantity(
            conn, user_id, preview["source_item_id"],
            preview["source_quantity_required"],
        ):
            conn.rollback()
            return {
                "success": False, "code": "not_enough_runes",
                "message": "❌ Потрібно 3 однакові руни одного типу й рівня.",
            }
        if not _consume_stack_quantity(
            conn, user_id, FIRIUS_TOKEN_ITEM_ID,
            RUNE_FUSION_TOKEN_QUANTITY,
        ):
            conn.rollback()
            return {
                "success": False, "code": "not_enough_tokens",
                "message": "❌ Для переробки потрібен 1 Жетон Фіріуса.",
            }
        added = _add_stack_quantity_in_transaction(
            conn, user_id, preview["result_item_id"], 1
        )
        if not added.get("success"):
            conn.rollback()
            return {
                "success": False, "code": added.get("code", "bag_full"),
                "message": (
                    "🎒 У сумці немає місця для результату переробки.\n\n"
                    "Руни та Жетон Фіріуса не були витрачені."
                ),
            }
        conn.commit()
        return {
            **preview,
            "success": True,
            "code": "fused",
            "message": (
                "✅ Переробку завершено!\n\n"
                f"Витрачено:\n"
                f"• {preview['source_name']} ×3\n"
                "• 🪙 Жетон Фіріуса ×1\n\n"
                f"Отримано:\n• {preview['result_name']} ×1\n\n"
                "Шанс успіху: 100%."
            ),
        }
    except Exception:
        conn.rollback()
        raise

# ==============================
# ROM 10.9.0 SIMPLE RUNE EXTRACTOR
# ==============================

def get_extractor_material_counts(user_id):
    db=_db()
    def total(item_id):
        return int(db.conn.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",
            (int(user_id),int(item_id))).fetchone()[0] or 0)
    return {"simple":total(RUNE_EXTRACTOR_ITEM_ID),"perfect":total(PERFECT_RUNE_EXTRACTOR_ITEM_ID)}


def get_extractor_equipment(user_id):
    db=_db()
    rows=db.conn.execute("""
        SELECT i.id,it.name,COUNT(ir.id)
        FROM inventory i JOIN items it ON it.id=i.item_id
        JOIN inventory_runes ir ON ir.inventory_id=i.id
        LEFT JOIN equipment_slots es ON es.user_id=i.user_id AND es.inventory_id=i.id
        WHERE i.user_id=? AND it.category='equipment' AND es.inventory_id IS NULL
        GROUP BY i.id,it.name HAVING COUNT(ir.id)>0 ORDER BY i.id
    """,(int(user_id),)).fetchall()
    return [{"inventory_id":int(r[0]),"name":str(r[1]),"rune_count":int(r[2])} for r in rows]


def get_extractor_preview(user_id,equipment_inventory_id):
    db=_db(); user_id=int(user_id); equipment_inventory_id=int(equipment_inventory_id)
    row=db.conn.execute("""
        SELECT i.user_id,it.name,it.category,
        EXISTS(SELECT 1 FROM equipment_slots es WHERE es.user_id=i.user_id AND es.inventory_id=i.id)
        FROM inventory i JOIN items it ON it.id=i.item_id WHERE i.id=?
    """,(equipment_inventory_id,)).fetchone()
    if not row:return {"success":False,"code":"not_found","message":"❌ Предмет спорядження не знайдено."}
    if int(row[0])!=user_id:return {"success":False,"code":"not_owner","message":"❌ Цей предмет не належить персонажу."}
    if str(row[2])!='equipment':return {"success":False,"code":"not_equipment","message":"❌ Екстрактор застосовується лише до спорядження."}
    if bool(row[3]):return {"success":False,"code":"equipped","message":"❌ Перед вилученням рун потрібно зняти предмет."}
    runes=get_inventory_runes(equipment_inventory_id)
    if not runes:return {"success":False,"code":"no_runes","message":"❌ У цьому предметі немає вставлених рун."}
    from data.runes import RUNE_LEVEL_ROMAN,RUNE_STAT_NAMES
    named=[]
    for rune in runes:
        named.append({**rune,"name":f"💠 Руна {RUNE_STAT_NAMES.get(rune['stat'],rune['stat'])} {RUNE_LEVEL_ROMAN.get(int(rune['level']),rune['level'])}"})
    return {"success":True,"equipment_inventory_id":equipment_inventory_id,"equipment_name":str(row[1]),
            "runes":named,"rune_count":len(named),"materials":get_extractor_material_counts(user_id)}


def _consume_extractor_stack(conn,user_id,item_id):
    row=conn.execute("SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND quantity>0 ORDER BY id LIMIT 1",
                     (int(user_id),int(item_id))).fetchone()
    if not row:return False
    if int(row[1])==1:conn.execute("DELETE FROM inventory WHERE id=?",(int(row[0]),))
    else:conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=?",(int(row[0]),))
    return True


def use_simple_rune_extractor(user_id,equipment_inventory_id,random_choice=None):
    import random
    db=_db(); conn=db.conn
    try:
        conn.execute('BEGIN IMMEDIATE')
        preview=get_extractor_preview(user_id,equipment_inventory_id)
        if not preview.get('success'):conn.rollback();return preview
        if preview['materials']['simple']<1:
            conn.rollback();return {"success":False,"code":"no_extractor","message":"❌ В інвентарі немає Простого Екстрактора рун."}
        selected=(random_choice or random.choice)(list(preview['runes']))
        if selected not in preview['runes']:raise RuntimeError('invalid random rune')
        if not _consume_extractor_stack(conn,user_id,RUNE_EXTRACTOR_ITEM_ID):
            conn.rollback();return {"success":False,"code":"no_extractor","message":"❌ Простий Екстрактор уже відсутній."}
        if conn.execute("DELETE FROM inventory WHERE id=? AND user_id=?",(int(equipment_inventory_id),int(user_id))).rowcount!=1:
            conn.rollback();return {"success":False,"code":"not_found","message":"❌ Предмет уже відсутній."}
        conn.execute("DELETE FROM inventory_runes WHERE inventory_id=?",(int(equipment_inventory_id),))
        added=_add_stack_quantity_in_transaction(conn,user_id,int(selected['rune_item_id']),1)
        if not added.get('success'):
            conn.rollback();return {"success":False,"code":"bag_full","message":"🎒 Немає місця для поверненої руни. Нічого не витрачено."}
        conn.commit(); lost=max(0,preview['rune_count']-1)
        return {"success":True,"code":"extracted","returned_rune_item_id":int(selected['rune_item_id']),
                "message":f"✅ Просте вилучення завершено!\n\nПовернено:\n• {selected['name']} ×1\n\nЗнищено:\n• {preview['equipment_name']}\n• Інших рун: {lost}\n• 🧰 Простий Екстрактор рун ×1"}
    except Exception:
        conn.rollback();raise

# ==============================
# ROM 10.9.2 CANONICAL RUNE EQUIPMENT DISPLAY NAMES
# ==============================

_RUNE_ARMOR_DISPLAY_LABELS_10_9_2 = {
    "cloth": "Тканина",
    "leather": "Шкіра",
    "chain": "Кольчуга",
    "plate": "Лати",
}
_RUNE_ARMOR_DISPLAY_SLOTS_10_9_2 = {
    "helmet", "shoulders", "chest", "gloves", "legs", "boots"
}


def _insert_armor_type_into_equipment_name_10_9_2(name, type_label):
    """Mirror Inventory UI placement: Name 5 рівня -> Name [Type] 5 рівня."""
    name = str(name or "")
    type_label = str(type_label or "")
    if not name or not type_label or f"[{type_label}]" in name:
        return name
    marker = " рівня"
    if marker in name:
        index = name.rfind(marker)
        before_level = name[:index]
        after_level = name[index:]
        parts = before_level.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]} [{type_label}] {parts[1]}{after_level}"
    return f"{name} [{type_label}]"


def get_rune_equipment_display_name(inventory_id, fallback_name=None):
    """Return the same armor-type display name used by the normal inventory."""
    db = _db()
    row = db.conn.execute(
        """
        SELECT it.name, COALESCE(it.slot_key,''), COALESCE(it.armor_type,'')
        FROM inventory i JOIN items it ON it.id=i.item_id
        WHERE i.id=?
        """,
        (int(inventory_id),),
    ).fetchone()
    if not row:
        return str(fallback_name or "")
    name = str((fallback_name if fallback_name is not None else row[0]) or row[0] or "")
    slot_key = str(row[1] or "")
    armor_type = str(row[2] or "").strip().lower()
    if slot_key not in _RUNE_ARMOR_DISPLAY_SLOTS_10_9_2:
        return name
    type_label = _RUNE_ARMOR_DISPLAY_LABELS_10_9_2.get(armor_type, "")
    return _insert_armor_type_into_equipment_name_10_9_2(name, type_label)


_RUNE_DISPLAY_BASE_SLOT_INFO_10_9_2 = get_equipment_rune_slot_info


def get_equipment_rune_slot_info(user_id, inventory_id):
    result = _RUNE_DISPLAY_BASE_SLOT_INFO_10_9_2(user_id, inventory_id)
    if result.get("success"):
        result = dict(result)
        result["name"] = get_rune_equipment_display_name(
            inventory_id, result.get("name")
        )
    return result


_RUNE_DISPLAY_BASE_EXTRACTOR_EQUIPMENT_10_9_2 = get_extractor_equipment


def get_extractor_equipment(user_id):
    result = _RUNE_DISPLAY_BASE_EXTRACTOR_EQUIPMENT_10_9_2(user_id)
    normalized = []
    for item in result:
        item = dict(item)
        item["name"] = get_rune_equipment_display_name(
            item["inventory_id"], item.get("name")
        )
        normalized.append(item)
    return normalized


_RUNE_DISPLAY_BASE_EXTRACTOR_PREVIEW_10_9_2 = get_extractor_preview


def get_extractor_preview(user_id, equipment_inventory_id):
    result = _RUNE_DISPLAY_BASE_EXTRACTOR_PREVIEW_10_9_2(
        user_id, equipment_inventory_id
    )
    if result.get("success"):
        result = dict(result)
        result["equipment_name"] = get_rune_equipment_display_name(
            equipment_inventory_id, result.get("equipment_name")
        )
    return result

# ==============================
# ROM 10.10.0 PERFECT RUNE EXTRACTOR
# ==============================


def use_perfect_rune_extractor(user_id, equipment_inventory_id):
    """Return every inserted rune; destroy equipment and one Perfect Extractor."""
    db = _db()
    conn = db.conn
    try:
        conn.execute("BEGIN IMMEDIATE")
        preview = get_extractor_preview(user_id, equipment_inventory_id)
        if not preview.get("success"):
            conn.rollback()
            return preview

        if int(preview["materials"].get("perfect", 0) or 0) < 1:
            conn.rollback()
            return {
                "success": False,
                "code": "no_perfect_extractor",
                "message": "❌ В інвентарі немає Досконалого Екстрактора рун.",
            }

        if not _consume_extractor_stack(
            conn, user_id, PERFECT_RUNE_EXTRACTOR_ITEM_ID
        ):
            conn.rollback()
            return {
                "success": False,
                "code": "no_perfect_extractor",
                "message": "❌ Досконалий Екстрактор уже відсутній в інвентарі.",
            }

        deleted = conn.execute(
            "DELETE FROM inventory WHERE id=? AND user_id=?",
            (int(equipment_inventory_id), int(user_id)),
        ).rowcount
        if deleted != 1:
            conn.rollback()
            return {
                "success": False,
                "code": "not_found",
                "message": "❌ Предмет уже відсутній в інвентарі.",
            }

        conn.execute(
            "DELETE FROM inventory_runes WHERE inventory_id=?",
            (int(equipment_inventory_id),),
        )

        returned = []
        for rune in preview["runes"]:
            added = _add_stack_quantity_in_transaction(
                conn,
                user_id,
                int(rune["rune_item_id"]),
                1,
            )
            if not added.get("success"):
                conn.rollback()
                return {
                    "success": False,
                    "code": added.get("code", "bag_full"),
                    "message": (
                        "🎒 У сумці недостатньо місця для повернення всіх рун.\n\n"
                        "Предмет, руни та Досконалий Екстрактор не були витрачені."
                    ),
                }
            returned.append({
                "rune_item_id": int(rune["rune_item_id"]),
                "name": rune["name"],
                "quantity": 1,
            })

        conn.commit()
        returned_lines = "\n".join(
            f"• {rune['name']} ×1" for rune in returned
        )
        return {
            "success": True,
            "code": "perfect_extracted",
            "equipment_name": preview["equipment_name"],
            "returned_runes": returned,
            "returned_count": len(returned),
            "message": (
                "✅ Досконале вилучення завершено!\n\n"
                f"Повернено всі руни:\n{returned_lines}\n\n"
                f"Знищено:\n• {preview['equipment_name']}\n"
                "• ✨ Досконалий Екстрактор рун ×1"
            ),
        }
    except Exception:
        conn.rollback()
        raise

# ==============================
# ROM 10.11.0 RUNE DROP AND BALANCE
# ==============================

def classify_rune_drop_enemy(mob):
    """Canonical priority: boss > elite > normal."""
    mob = mob or {}
    mob_type = str(mob.get("mob_type", mob.get("enemy_type", "")) or "").lower()
    if bool(mob.get("is_boss", False) or mob.get("boss", False)) or mob_type == "boss":
        return "boss"
    if bool(mob.get("is_elite", False) or mob.get("elite", False)) or mob_type == "elite":
        return "elite"
    return "normal"


def _weighted_choice_10_11_0(weighted_values, random_value):
    point = max(0.0, min(0.999999999999, float(random_value)))
    cumulative = 0.0
    for value, weight in weighted_values:
        cumulative += float(weight)
        if point < cumulative:
            return value
    return weighted_values[-1][0]


def _legacy_roll_rune_drop_11_10_0(mob, random_func=None):
    """Pure roll. Returns at most one canonical rune; never levels IV-V."""
    import random
    from data.rune_drop_balance import (
        RUNE_DROP_CHANCES, RUNE_LEVEL_WEIGHTS, RUNE_STAT_WEIGHTS,
    )
    rng = random_func or random.random
    enemy_type = classify_rune_drop_enemy(mob)
    chance = float(RUNE_DROP_CHANCES[enemy_type])
    roll = float(rng())
    if roll >= chance:
        return {"dropped": False, "enemy_type": enemy_type, "chance": chance, "roll": roll}
    level = int(_weighted_choice_10_11_0(RUNE_LEVEL_WEIGHTS[enemy_type], rng()))
    stat = str(_weighted_choice_10_11_0(RUNE_STAT_WEIGHTS, rng()))
    item_id = get_rune_item_id(stat, level)
    definition = get_rune_definition(item_id)
    return {
        "dropped": True, "enemy_type": enemy_type, "chance": chance, "roll": roll,
        "item_id": int(item_id), "name": definition["name"], "stat": stat,
        "level": level, "quantity": 1,
    }


def award_rune_drop(user_id, mob, random_func=None):
    """Roll once and add at most one rune without replacing ordinary loot."""
    result = roll_rune_drop(mob, random_func=random_func)
    if not result.get("dropped"):
        return result
    db = _db()
    added = db.add_item(int(user_id), int(result["item_id"]), 1)
    result = dict(result)
    result["added"] = int(added.get("added", 0) or 0)
    result["lost"] = int(added.get("lost", 0) or 0)
    result["success"] = result["added"] == 1
    result["message"] = (
        f"💠 Здобуто руну: {result['name']} ×1"
        if result["success"] else
        f"⚠️ Випала руна, але в сумці не було місця: {result['name']}"
    )
    return result


def simulate_rune_drops(enemy_type, trials, seed=None):
    """Read-only deterministic simulation; never awards inventory items."""
    import random
    enemy_type = str(enemy_type or "").strip().lower()
    if enemy_type not in ("normal", "elite", "boss"):
        return {"success": False, "message": "❌ Тип ворога: normal, elite або boss."}
    try:
        trials = int(trials)
    except Exception:
        return {"success": False, "message": "❌ Кількість симуляцій має бути числом."}
    if trials < 1 or trials > 100000:
        return {"success": False, "message": "❌ Кількість симуляцій: від 1 до 100000."}
    rng = random.Random(seed)
    mob = {"mob_type": enemy_type, "is_elite": enemy_type == "elite", "is_boss": enemy_type == "boss"}
    levels = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    stats = {"STR": 0, "STA": 0, "DEX": 0, "INT": 0, "WIS": 0}
    dropped = 0
    for _ in range(trials):
        result = roll_rune_drop(mob, random_func=rng.random)
        if result.get("dropped"):
            dropped += 1; levels[result["level"]] += 1; stats[result["stat"]] += 1
    return {"success": True, "enemy_type": enemy_type, "trials": trials,
            "dropped": dropped, "actual_rate": dropped / trials,
            "levels": levels, "stats": stats}

# ==============================
# ROM 10.13.0 RUNE MASTER EXTRACTOR SHOP
# ==============================


def get_rune_master_shop_state(user_id):
    """Read-only Rune Master shop state for the current character."""
    from data.runes import (
        PERFECT_RUNE_EXTRACTOR_CRYSTAL_SHOP_ENABLED,
        SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE,
        SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED,
    )
    db = _db()
    row = db.conn.execute(
        "SELECT COALESCE(gold,0) FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    counts = get_extractor_material_counts(user_id)
    return {
        "success": row is not None,
        "gold": round(float(row[0] or 0), 2) if row else 0.0,
        "simple_price": float(SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE),
        "simple_enabled": bool(SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED),
        "simple_owned": int(counts.get("simple", 0) or 0),
        "perfect_owned": int(counts.get("perfect", 0) or 0),
        "perfect_crystal_enabled": bool(PERFECT_RUNE_EXTRACTOR_CRYSTAL_SHOP_ENABLED),
    }


def buy_simple_rune_extractor(user_id, quantity=1):
    """Atomically buy Simple Rune Extractors for gold."""
    from data.runes import (
        SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE,
        SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED,
    )
    db = _db()
    conn = db.conn
    try:
        user_id = int(user_id)
        quantity = int(quantity)
    except Exception:
        return {
            "success": False,
            "code": "invalid_quantity",
            "message": "❌ Некоректна кількість Екстракторів.",
        }
    if quantity < 1 or quantity > 100:
        return {
            "success": False,
            "code": "invalid_quantity",
            "message": "❌ За одну покупку можна придбати від 1 до 100 Екстракторів.",
        }
    if not SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED:
        return {
            "success": False,
            "code": "shop_disabled",
            "message": "❌ Продаж Простих Екстракторів тимчасово вимкнено.",
        }

    unit_price = float(SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE)
    total_price = round(unit_price * quantity, 2)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT COALESCE(gold,0) FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row:
            conn.rollback()
            return {
                "success": False,
                "code": "user_not_found",
                "message": "❌ Персонажа не знайдено.",
            }
        current_gold = round(float(row[0] or 0), 2)
        if current_gold + 1e-9 < total_price:
            conn.rollback()
            return {
                "success": False,
                "code": "not_enough_gold",
                "gold": current_gold,
                "required": total_price,
                "message": (
                    "❌ Недостатньо золота.\n\n"
                    f"Потрібно: {total_price:g} золота\n"
                    f"Доступно: {current_gold:g} золота"
                ),
            }

        added = _add_stack_quantity_in_transaction(
            conn,
            user_id,
            RUNE_EXTRACTOR_ITEM_ID,
            quantity,
        )
        if not added.get("success"):
            conn.rollback()
            return {
                "success": False,
                "code": added.get("code", "bag_full"),
                "message": (
                    "🎒 У сумці немає місця для Простого Екстрактора.\n\n"
                    "Золото не було витрачено."
                ),
            }

        updated = conn.execute(
            "UPDATE users SET gold=ROUND(gold-?,2) "
            "WHERE user_id=? AND gold>=?",
            (total_price, user_id, total_price),
        )
        if updated.rowcount != 1:
            conn.rollback()
            return {
                "success": False,
                "code": "gold_changed",
                "message": "❌ Баланс золота змінився. Покупку скасовано.",
            }
        new_gold = round(float(conn.execute(
            "SELECT gold FROM users WHERE user_id=?", (user_id,)
        ).fetchone()[0] or 0), 2)
        conn.commit()
        return {
            "success": True,
            "code": "purchased",
            "item_id": RUNE_EXTRACTOR_ITEM_ID,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
            "gold": new_gold,
            "message": (
                "✅ Покупку завершено!\n\n"
                f"Отримано:\n• 🧰 Простий Екстрактор рун ×{quantity}\n\n"
                f"Витрачено: {total_price:g} золота\n"
                f"Залишок: {new_gold:g} золота"
            ),
        }
    except Exception:
        conn.rollback()
        raise

# ==============================
# ROM 11.2.0 CENTRAL DROP RUNE MIGRATION
# ==============================


def roll_rune_drop(mob, random_func=None):
    """Compatibility API now delegated to the central drop rune rule."""
    import random
    from systems.drop_system import roll_central_rune_drop

    rng = random_func or random.random
    central = roll_central_rune_drop(mob, rng)
    payload = central.get("payload") or {}
    if not central.get("rolled"):
        return {
            "dropped": False,
            "enemy_type": central["enemy_type"],
            "chance": payload.get("chance"),
            "roll": payload.get("roll"),
        }

    stat = str(payload["stat"])
    level = int(payload["level"])
    item_id = get_rune_item_id(stat, level)
    definition = get_rune_definition(item_id)
    return {
        "dropped": True,
        "enemy_type": central["enemy_type"],
        "chance": float(payload["chance"]),
        "roll": float(payload["roll"]),
        "item_id": int(item_id),
        "name": definition["name"],
        "stat": stat,
        "level": level,
        "quantity": 1,
    }

