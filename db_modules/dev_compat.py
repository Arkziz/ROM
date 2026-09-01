# ROM 17.17.1.5 WARRIOR SMALL SHIELD
# ROM 17.14.1.1 SEPARATE LEVEL REWARD MESSAGE AND DEV EXP SETTER
# ROM 17.12.1.1 DEV RESET HERO LOCK INITIALIZATION
"""DEV compatibility API restored from final legacy db.py definitions."""

import sqlite3

from .connection import conn, cursor, DEFAULT_BAG_SLOTS, SLOT_ORDER
from systems.item_id_allocator_system import allocate_generated_item_id

from .equipment import ensure_equipment_slots

from .generated_equipment import create_generated_equipment_item, create_generated_equipment_item_for_slot

from data.classes import CLASS_CONFIGS, CLASS_RESET_SPHERE_ITEM_ID

import sqlite3

import random

from data.equipment_profiles import (
    ARMOR_ALLOWED_BY_CLASS,
    ARMOR_EXTRA_STATS_BY_SLOT,
    ARMOR_TYPE_LABELS,
    EQUIPMENT_SLOTS,
    ITEM_SUBTYPE_LABELS,
    MAIN_HAND_ALLOWED_BY_CLASS,
    MAIN_HAND_PROFILES,
    OFF_HAND_ALLOWED_BY_CLASS,
    OFF_HAND_PROFILES,
)

def get_bag_capacity(user_id):
    cursor.execute("""
    SELECT bag_slots
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row or row[0] is None:
        return DEFAULT_BAG_SLOTS

    try:
        capacity = int(row[0] or DEFAULT_BAG_SLOTS)
    except Exception:
        capacity = DEFAULT_BAG_SLOTS
    return max(DEFAULT_BAG_SLOTS, capacity)

def get_inventory_used_slots(user_id):
    cursor.execute("""
    SELECT COUNT(*)
    FROM inventory
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return 0

    return row[0]

def get_exp_to_next_level(level):
    from data.player_progression import get_exp_to_next_level as _canonical
    return _canonical(level)

DYNAMIC_RARITY_ICONS = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "epic": "🟣"
}

DYNAMIC_STAT_MULTIPLIERS = {
    "common": 1.0,
    "uncommon": 1.35,
    "rare": 1.85,
    "epic": 2.60
}

DYNAMIC_SELL_MULTIPLIERS = {
    "common": 0.30,
    "uncommon": 0.90,
    "rare": 2.25,
    "epic": 6.00
}

DYNAMIC_SLOT_NAMES = {
    "main_hand": "Зброя",
    "off_hand": "Друга рука",
    "helmet": "Шолом",
    "shoulders": "Наплічники",
    "chest": "Обладунок",
    "gloves": "Рукавиці",
    "legs": "Поножі",
    "boots": "Чоботи",
    "necklace": "Амулет",
    "ring": "Кільце"
}

def get_dynamic_stat_value(item_level, rarity, base=1.0):
    multiplier = DYNAMIC_STAT_MULTIPLIERS.get(rarity, 1.0)
    value = int(round(item_level * base * multiplier))

    return max(1, value)

def get_dynamic_sell_price(item_level, rarity):
    multiplier = DYNAMIC_SELL_MULTIPLIERS.get(rarity, 0.30)

    return round(max(0.10, item_level * multiplier), 2)

def get_dynamic_armor_name(slot_key, rarity):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")
    base_name = DYNAMIC_SLOT_NAMES.get(slot_key, "Річ")

    return f"{icon} {base_name}"

def set_player_level_for_test(user_id, target_level):
    try:
        target_level = int(target_level)
    except Exception:
        return {
            "success": False,
            "message": "❌ Рівень має бути числом."
        }

    if target_level < 1:
        target_level = 1

    if target_level > 30:
        target_level = 30

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено. Спочатку натисни /start."
        }

    base_stat = 10 + (target_level - 1)

    cursor.execute("""
    UPDATE users
    SET
        level=?,
        exp=0,
        str=?,
        dex=?,
        intelligence=?,
        wis=?,
        sta=?
    WHERE user_id=?
    """, (
        target_level,
        base_stat,
        base_stat,
        base_stat,
        base_stat,
        base_stat,
        user_id
    ))

    conn.commit()

    new_max_hp = get_max_hp(user_id)

    cursor.execute("""
    UPDATE users
    SET
        max_hp=?,
        hp=?
    WHERE user_id=?
    """, (
        new_max_hp,
        new_max_hp,
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "level": target_level,
        "base_stat": base_stat,
        "max_hp": new_max_hp,
        "message": (
            f"✅ DEV: рівень персонажа встановлено.\n\n"
            f"🏆 Рівень: {target_level}\n"
            f"✨ Досвід: 0/{get_exp_to_next_level(target_level)}\n"
            f"💪 Базові характеристики: {base_stat}\n"
            f"❤️ HP: {new_max_hp}/{new_max_hp}"
        )
    }

def reset_player_level_for_test(user_id):
    return set_player_level_for_test(user_id, 1)

def set_gold_for_test(user_id, amount):
    """
    DEV-функція.
    Встановлює золото вручну.
    Приклади:
    /gold 100
    /gold 0
    """

    try:
        amount = float(amount)
    except Exception:
        return {
            "success": False,
            "message": "❌ Значення золота має бути числом."
        }

    if amount < 0:
        amount = 0

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено. Спочатку натисни /start."
        }

    cursor.execute("""
    UPDATE users
    SET gold=?
    WHERE user_id=?
    """, (amount, user_id))

    conn.commit()

    return {
        "success": True,
        "gold": amount,
        "message": f"✅ DEV: золото встановлено {amount:.2f} 🪙"
    }

_DEV_RESET_HERO_LOCK = None


def _get_dev_reset_hero_lock():
    global _DEV_RESET_HERO_LOCK
    if _DEV_RESET_HERO_LOCK is None:
        import threading
        _DEV_RESET_HERO_LOCK = threading.RLock()
    return _DEV_RESET_HERO_LOCK

def _dev_reset_table_exists(table_name):
    row = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (str(table_name),),
    ).fetchone()
    return bool(row)

def _dev_reset_table_columns(table_name):
    if not _dev_reset_table_exists(table_name):
        return set()
    return {str(row[1]) for row in cursor.execute(f'PRAGMA table_info("{table_name}")').fetchall()}

def _dev_reset_delete_by_user_columns(table_name, user_id, candidate_columns):
    columns = _dev_reset_table_columns(table_name)
    matched = [column for column in candidate_columns if column in columns]
    if not matched:
        return 0
    where_sql = " OR ".join(f'"{column}"=?' for column in matched)
    result = cursor.execute(
        f'DELETE FROM "{table_name}" WHERE {where_sql}',
        tuple(int(user_id) for _ in matched),
    )
    return max(0, int(result.rowcount or 0))

def reset_hero_for_test(user_id):
    """Atomically reset character progress without deleting the users parent row.

    Keeping users.user_id in place prevents RESTRICT foreign keys in trade and
    interaction history from breaking the reset. All mutations are enclosed in
    one BEGIN IMMEDIATE transaction. Every failure performs rollback so the
    shared SQLite connection cannot retain a write lock.
    """
    import time
    from datetime import datetime

    user_id = int(user_id)
    lock = _get_dev_reset_hero_lock()
    last_error = None

    with lock:
        for attempt in range(1, 4):
            stage = "prepare"
            deleted = {}
            try:
                try:
                    conn.rollback()
                except Exception:
                    pass

                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA busy_timeout=30000")
                stage = "begin_immediate"
                conn.execute("BEGIN IMMEDIATE")

                row = cursor.execute(
                    "SELECT user_id FROM users WHERE user_id=?",
                    (user_id,),
                ).fetchone()
                if not row:
                    conn.rollback()
                    return {
                        "success": False,
                        "message": "❌ Персонажа не знайдено. Спочатку натисни /start.",
                    }

                # Trade children must be removed before player_trades because
                # some installations can have foreign_keys disabled historically.
                stage = "trade_cleanup"
                trade_ids = []
                if _dev_reset_table_exists("player_trades"):
                    trade_ids = [
                        int(row[0])
                        for row in cursor.execute(
                            "SELECT id FROM player_trades WHERE initiator_user_id=? OR recipient_user_id=?",
                            (user_id, user_id),
                        ).fetchall()
                    ]
                if trade_ids:
                    placeholders = ",".join("?" for _ in trade_ids)
                    for table_name in (
                        "inventory_reservations",
                        "player_trade_offers",
                        "player_trade_events",
                        "player_trade_history",
                    ):
                        columns = _dev_reset_table_columns(table_name)
                        if "trade_id" in columns:
                            result = cursor.execute(
                                f'DELETE FROM "{table_name}" WHERE trade_id IN ({placeholders})',
                                tuple(trade_ids),
                            )
                            deleted[table_name] = deleted.get(table_name, 0) + max(0, int(result.rowcount or 0))
                    result = cursor.execute(
                        f'DELETE FROM player_trades WHERE id IN ({placeholders})',
                        tuple(trade_ids),
                    )
                    deleted["player_trades"] = max(0, int(result.rowcount or 0))

                stage = "user_child_cleanup"
                user_column_names = (
                    "user_id",
                    "owner_user_id",
                    "initiator_user_id",
                    "recipient_user_id",
                    "actor_user_id",
                    "challenger_user_id",
                    "recipient_id",
                    "initiator_id",
                    "player_one_user_id",
                    "player_two_user_id",
                    "winner_user_id",
                    "loser_user_id",
                )
                protected_tables = {"users", "items", "inventory", "equipment_slots", "inventory_runes", "crystal_wallets", "crystal_transactions"}
                table_names = [
                    str(row[0])
                    for row in cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                ]
                for table_name in table_names:
                    if table_name in protected_tables:
                        continue
                    count = _dev_reset_delete_by_user_columns(table_name, user_id, user_column_names)
                    if count:
                        deleted[table_name] = deleted.get(table_name, 0) + count

                stage = "inventory_dependency_cleanup"
                if _dev_reset_table_exists("inventory_runes"):
                    result = cursor.execute(
                        "DELETE FROM inventory_runes WHERE inventory_id IN (SELECT id FROM inventory WHERE user_id=?)",
                        (user_id,),
                    )
                    deleted["inventory_runes"] = max(0, int(result.rowcount or 0))
                if _dev_reset_table_exists("inventory_reservations"):
                    result = cursor.execute(
                        "DELETE FROM inventory_reservations WHERE user_id=? OR inventory_id IN (SELECT id FROM inventory WHERE user_id=?)",
                        (user_id, user_id),
                    )
                    deleted["inventory_reservations"] = deleted.get("inventory_reservations", 0) + max(0, int(result.rowcount or 0))
                if _dev_reset_table_exists("equipment_slots"):
                    result = cursor.execute("DELETE FROM equipment_slots WHERE user_id=?", (user_id,))
                    deleted["equipment_slots"] = max(0, int(result.rowcount or 0))
                if _dev_reset_table_exists("inventory"):
                    result = cursor.execute("DELETE FROM inventory WHERE user_id=?", (user_id,))
                    deleted["inventory"] = max(0, int(result.rowcount or 0))

                stage = "user_in_place_reset"
                now_text = datetime.now().isoformat()
                defaults = {
                    "hp": 170,
                    "max_hp": 170,
                    "level": 1,
                    "exp": 0,
                    "gold": 0.0,
                    "kills": 0,
                    "bag_slots": max(int(globals().get("DEFAULT_BAG_SLOTS", 60)), int(get_bag_capacity(user_id))),  # ROM 17.32.1 preserve account entitlement
                    "current_location": "start_path",
                    "str": 10,
                    "dex": 10,
                    "intelligence": 10,
                    "wis": 10,
                    "sta": 10,
                    "equipped_weapon": None,
                    "equipped_armor": None,
                    "daily_contracts_completed": 0,
                    "daily_contract_date": "",
                    "daily_hunts": 0,
                    "daily_hunts_date": "",
                    "energy": 0,
                    "last_energy_update": now_text,
                    "energy_full_notified": 1,
                    "last_hp_regen_update": now_text,
                    "hp_full_notified": 1,
                    "character_name": "",
                    "character_class": "",
                    "class_selected_at": "",
                    "class_change_available": 0,
                    "mp": 0,
                    "max_mp": 0,
                    "last_regen_at": now_text,
                    "last_activity_at": None,
                }
                user_columns = _dev_reset_table_columns("users")
                assignments = []
                values = []
                for column, value in defaults.items():
                    if column in user_columns:
                        assignments.append(f'"{column}"=?')
                        values.append(value)
                if not assignments:
                    raise RuntimeError("users table has no resettable columns")
                values.append(user_id)
                cursor.execute(
                    f'UPDATE users SET {", ".join(assignments)} WHERE user_id=?',
                    tuple(values),
                )

                stage = "commit"
                conn.commit()

                # Recreate empty slots only after the atomic reset committed.
                stage = "post_commit_slots"
                ensure_equipment_slots(user_id)

                foreign_key_errors = cursor.execute("PRAGMA foreign_key_check").fetchall()
                if foreign_key_errors:
                    return {
                        "success": False,
                        "message": (
                            "❌ DEV reset completed, але foreign_key_check виявив помилки. "
                            "Не продовжуй тестування до recovery."
                        ),
                        "foreign_key_errors": [tuple(row) for row in foreign_key_errors],
                    }

                return {
                    "success": True,
                    "deleted": deleted,
                    "message": (
                        "✅ DEV: герой повністю скинутий.\n\n"
                        "Створено нового персонажа з нуля:\n"
                        "🏆 Рівень: 1\n"
                        "✨ EXP: 0\n"
                        "🪙 Золото: 0\n"
                        "🎒 Інвентар очищено\n"
                        "🛡️ Спорядження і руни очищено\n"
                        "📜 Контракти та активні взаємодії очищено\n"
                        "📆 Щоденні завдання очищено\n\n"
                        "✍️ Введи нове ім’я персонажа."
                    ),
                }

            except Exception as error:
                last_error = error
                try:
                    conn.rollback()
                except Exception:
                    pass
                locked = isinstance(error, sqlite3.OperationalError) and "locked" in str(error).lower()
                if locked and attempt < 3:
                    time.sleep(0.35 * attempt)
                    continue
                return {
                    "success": False,
                    "stage": stage,
                    "attempt": attempt,
                    "message": f"❌ DEV reset error at {stage}: {error}",
                }

    return {
        "success": False,
        "message": f"❌ DEV reset error: {last_error}",
    }

def init_dynamic_equipment_system():
    migrations = [
        ("items", "item_level", "INTEGER DEFAULT 1"),
        ("items", "is_generated", "INTEGER DEFAULT 0"),
        ("items", "item_subtype", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()

def add_stat_value(stats, stat_key, value):
    if stat_key == "str":
        stats["bonus_str"] += value
    elif stat_key == "dex":
        stats["bonus_dex"] += value
    elif stat_key == "int":
        stats["bonus_int"] += value
    elif stat_key == "wis":
        stats["bonus_wis"] += value
    elif stat_key == "sta":
        stats["bonus_sta"] += value

def get_random_main_hand_profile():
    return random.choice(list(MAIN_HAND_PROFILES.keys()))

def get_random_off_hand_profile():
    return random.choice(list(OFF_HAND_PROFILES.keys()))

def get_profile_for_generated_item(slot_key, item_profile=None):
    if slot_key == "main_hand":
        if item_profile in MAIN_HAND_PROFILES:
            return item_profile

        return get_random_main_hand_profile()

    if slot_key == "off_hand":
        if item_profile in OFF_HAND_PROFILES:
            return item_profile

        return get_random_off_hand_profile()

    return ""

def get_dynamic_weapon_name(slot_key, rarity, weapon_hands=1, item_profile=None):
    icon = DYNAMIC_RARITY_ICONS.get(rarity, "⚪")

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])
        return f"{icon} {profile['name']}"

    if slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])
        return f"{icon} {profile['name']}"

    return f"{icon} Зброя"

def generate_dynamic_equipment_stats(slot_key, item_level, rarity, weapon_hands=1, item_profile=None):
    stats = {
        "bonus_str": 0,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "pdef": 0,
        "mdef": 0
    }

    # ==============================
    # MAIN HAND
    # ==============================

    if slot_key == "main_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = MAIN_HAND_PROFILES.get(profile_key, MAIN_HAND_PROFILES["sword_1h"])

        main_stat = profile["main_stats"][0]
        base_multiplier = 1.00

        if profile["hands"] == 2:
            base_multiplier = 1.20

        value = get_dynamic_stat_value(item_level, rarity, base_multiplier)
        add_stat_value(stats, main_stat, value)

        extra_pool = profile["extra_stats"]

    # ==============================
    # OFF HAND
    # ==============================

    elif slot_key == "off_hand":
        profile_key = get_profile_for_generated_item(slot_key, item_profile)
        profile = OFF_HAND_PROFILES.get(profile_key, OFF_HAND_PROFILES["shield"])

        if profile_key == "shield":
            stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        elif profile_key == "warrior_shield":
            # 60% of Knight shield PDEF: 1.35 * 0.60 = 0.81.
            stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.81)
            stats["bonus_str"] = get_dynamic_stat_value(item_level, rarity, 0.65)
            stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.35)

        elif profile_key == "talisman":
            stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.35)
            stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.65)

        elif profile_key == "dagger":
            stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.95)
            stats["bonus_str"] = get_dynamic_stat_value(item_level, rarity, 0.35)

        extra_pool = profile["extra_stats"]

    # ==============================
    # ARMOR SLOTS
    # ==============================

    elif slot_key == "helmet":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.80)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.40)

        bonus = random.choice(["sta", "wis", "dex"])
        value = get_dynamic_stat_value(item_level, rarity, 0.25)
        add_stat_value(stats, bonus, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "shoulders":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.00)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.25)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "chest":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.60)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.35)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.55)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "gloves":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.55)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.60)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    elif slot_key == "legs":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 1.20)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.30)
        stats["bonus_sta"] = get_dynamic_stat_value(item_level, rarity, 0.45)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["sta"])

    elif slot_key == "boots":
        stats["pdef"] = get_dynamic_stat_value(item_level, rarity, 0.45)
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 0.20)
        stats["bonus_dex"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["dex"])

    # ==============================
    # JEWELRY
    # ==============================

    elif slot_key == "necklace":
        stats["mdef"] = get_dynamic_stat_value(item_level, rarity, 1.30)
        stats["bonus_wis"] = get_dynamic_stat_value(item_level, rarity, 0.80)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["wis", "int"])

    elif slot_key == "ring":
        stat_choice = random.choice(["str", "dex", "int", "wis", "sta"])
        value = get_dynamic_stat_value(item_level, rarity, 0.90)
        add_stat_value(stats, stat_choice, value)

        extra_pool = ARMOR_EXTRA_STATS_BY_SLOT.get(slot_key, ["str", "dex", "int", "wis", "sta"])

    else:
        extra_pool = ["str", "dex", "int", "wis", "sta"]

    # ==============================
    # EXTRA BONUSES BY RARITY
    # ==============================

    if rarity in ["uncommon", "rare", "epic"]:
        bonus_count = 1
        min_bonus = 2

        if rarity == "rare":
            bonus_count = 2
            min_bonus = 3

        if rarity == "epic":
            bonus_count = 3
            min_bonus = 4

        for _ in range(bonus_count):
            bonus_type = random.choice(extra_pool)

            bonus_value = get_dynamic_stat_value(item_level, rarity, 0.30)
            bonus_value = max(min_bonus, bonus_value)

            add_stat_value(stats, bonus_type, bonus_value)

    return stats

def seed_class_reset_sphere_item():
    """
    🔮 Сфера нового шляху.
    Предмет для майбутньої зміни класу.
    Зараз додаємо в базу, щоб можна було видавати через DEV і тестувати інвентар.
    """

    try:
        cursor.execute("""
        INSERT INTO items (
            id,
            name,
            type,
            rarity,
            category,
            slot_key,
            weapon_hands,
            max_stack,
            sell_price,
            bonus_str,
            bonus_dex,
            bonus_int,
            bonus_wis,
            bonus_sta,
            pdef,
            mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,
            bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,
            bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,
            bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,
            mdef=excluded.mdef
        """, (
            CLASS_RESET_SPHERE_ITEM_ID,
            "🔮 Сфера нового шляху",
            "class_reset",
            "epic",
            "potion",
            None,
            1,
            10,
            0.0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        ))

        conn.commit()
    except Exception:
        pass

ARMOR_SLOTS = [
    "helmet",
    "shoulders",
    "chest",
    "gloves",
    "legs",
    "boots"
]

def init_class_equipment_restrictions_system():
    """
    Додає службове поле armor_type для класових обмежень броні.

    weapon_family окремо НЕ додаємо.
    У поточній системі роль weapon_family виконує items.item_subtype.
    """

    migrations = [
        ("items", "armor_type", "TEXT DEFAULT ''"),
    ]

    for table, column, column_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()

def normalize_equipment_restriction_value(value):
    if value is None:
        return ""

    return str(value).strip()

def get_armor_type_label(armor_type):
    armor_type = normalize_equipment_restriction_value(armor_type)
    return ARMOR_TYPE_LABELS.get(armor_type, armor_type or "Універсальний")

def get_item_subtype_label(item_subtype):
    item_subtype = normalize_equipment_restriction_value(item_subtype)
    return ITEM_SUBTYPE_LABELS.get(item_subtype, item_subtype or "Універсальний")

ARMOR_DEFENSE_DISTRIBUTION_PROFILES = {
    "cloth": {
        # Тканина: мало фізичного, багато магічного.
        "pdef_share": 0.30,
        "mdef_share": 0.70,
        "total_multiplier": 1.00
    },
    "leather": {
        # Шкіра: близько до балансу, трохи більше фізичного.
        "pdef_share": 0.55,
        "mdef_share": 0.45,
        "total_multiplier": 1.05
    },
    "chain": {
        # Кольчуга: високий фізичний, нижчий магічний.
        "pdef_share": 0.75,
        "mdef_share": 0.25,
        "total_multiplier": 1.10
    },
    "plate": {
        # Лати: максимум фізичного, мінімум магічного.
        "pdef_share": 0.88,
        "mdef_share": 0.12,
        "total_multiplier": 1.15
    }
}

ARMOR_PRIMARY_STAT_PROFILES = {
    # Тканина для мага / жерця:
    # інтелект, мудрість, трохи витривалості.
    "cloth": {
        "primary_weights": [
            ("int", 40),
            ("wis", 40),
            ("sta", 20)
        ],
        "secondary_weights": [
            ("wis", 45),
            ("int", 45),
            ("sta", 10)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Шкіра для скаута / розбійника:
    # спритність, сила, трохи витривалості.
    "leather": {
        "primary_weights": [
            ("dex", 50),
            ("str", 30),
            ("sta", 20)
        ],
        "secondary_weights": [
            ("sta", 45),
            ("str", 35),
            ("dex", 20)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Кольчуга для воїна:
    # сила і витривалість.
    "chain": {
        "primary_weights": [
            ("str", 55),
            ("sta", 40),
            ("dex", 5)
        ],
        "secondary_weights": [
            ("sta", 55),
            ("str", 40),
            ("dex", 5)
        ],
        "main_multiplier": 1.00,
        "secondary_multiplier": 0.50
    },

    # Лати для лицаря:
    # витривалість головна, сила друга.
    "plate": {
        "primary_weights": [
            ("sta", 65),
            ("str", 35)
        ],
        "secondary_weights": [
            ("str", 70),
            ("sta", 30)
        ],
        "main_multiplier": 1.25,
        "secondary_multiplier": 0.50
    }
}

def pick_weighted_stat(weighted_stats, exclude_stat=None):
    """
    Вибирає характеристику за вагами.
    """

    filtered = []

    for stat_key, weight in weighted_stats:
        if exclude_stat is not None and stat_key == exclude_stat:
            continue

        filtered.append((stat_key, weight))

    if not filtered:
        filtered = weighted_stats

    if not filtered:
        return ""

    total_weight = sum(weight for _, weight in filtered)

    if total_weight <= 0:
        return filtered[0][0]

    roll = random.randint(1, total_weight)
    current = 0

    for stat_key, weight in filtered:
        current += weight

        if roll <= current:
            return stat_key

    return filtered[-1][0]

def add_primary_stat_to_stats(stats, stat_key, value):
    """
    Додає основну характеристику у stats.
    """

    value = int(value or 0)

    if value <= 0:
        return

    if stat_key == "str":
        stats["bonus_str"] += value

    elif stat_key == "dex":
        stats["bonus_dex"] += value

    elif stat_key == "int":
        stats["bonus_int"] += value

    elif stat_key == "wis":
        stats["bonus_wis"] += value

    elif stat_key == "sta":
        stats["bonus_sta"] += value

def get_existing_primary_stat_budget(stats):
    """
    Рахує поточний бюджет основних характеристик.
    Наприклад chest 8 common дає bonus_sta = 4, отже budget = 4.
    """

    return (
        int(stats.get("bonus_str", 0) or 0)
        + int(stats.get("bonus_dex", 0) or 0)
        + int(stats.get("bonus_int", 0) or 0)
        + int(stats.get("bonus_wis", 0) or 0)
        + int(stats.get("bonus_sta", 0) or 0)
    )

def clear_primary_stat_bonuses(stats):
    """
    Очищає старі slot-based характеристики.
    """

    stats["bonus_str"] = 0
    stats["bonus_dex"] = 0
    stats["bonus_int"] = 0
    stats["bonus_wis"] = 0
    stats["bonus_sta"] = 0

def apply_armor_type_primary_stat_profile_to_stats(stats, armor_type):
    """
    Перерозподіляє основні характеристики броні залежно від armor_type.

    cloth   -> INT / WIS / STA
    leather -> DEX / STR / STA
    chain   -> STR / STA / рідко DEX
    plate   -> STA / STR
    """

    armor_type = normalize_equipment_restriction_value(armor_type)

    if not armor_type:
        return stats

    profile = ARMOR_PRIMARY_STAT_PROFILES.get(armor_type)

    if not profile:
        return stats

    existing_budget = get_existing_primary_stat_budget(stats)

    if existing_budget <= 0:
        return stats

    clear_primary_stat_bonuses(stats)

    main_multiplier = float(profile.get("main_multiplier", 1.0))
    secondary_multiplier = float(profile.get("secondary_multiplier", 0.5))

    primary_value = int(round(existing_budget * main_multiplier))
    secondary_value = int(round(existing_budget * secondary_multiplier))

    primary_value = max(1, primary_value)

    if existing_budget >= 2:
        secondary_value = max(1, secondary_value)
    else:
        secondary_value = 0

    primary_stat = pick_weighted_stat(
        profile.get("primary_weights", []),
        exclude_stat=None
    )

    secondary_stat = None

    if secondary_value > 0:
        secondary_stat = pick_weighted_stat(
            profile.get("secondary_weights", []),
            exclude_stat=primary_stat
        )

    add_primary_stat_to_stats(
        stats=stats,
        stat_key=primary_stat,
        value=primary_value
    )

    if secondary_stat:
        add_primary_stat_to_stats(
            stats=stats,
            stat_key=secondary_stat,
            value=secondary_value
        )

    return stats

def apply_armor_type_defense_profile_to_stats(stats, armor_type):
    """
    Центральна функція профілю броні.

    Робить 2 речі:
    1. Перерозподіляє PDEF/MDEF залежно від armor_type.
    2. Перерозподіляє основні характеристики залежно від armor_type.
    """

    armor_type = normalize_equipment_restriction_value(armor_type)

    if not armor_type:
        return stats

    # ==============================
    # 1. PDEF / MDEF redistribution
    # ==============================

    defense_profile = ARMOR_DEFENSE_DISTRIBUTION_PROFILES.get(armor_type)

    if defense_profile:
        base_pdef = int(stats.get("pdef", 0) or 0)
        base_mdef = int(stats.get("mdef", 0) or 0)
        base_total = base_pdef + base_mdef

        if base_total > 0:
            total_multiplier = float(defense_profile.get("total_multiplier", 1.0))
            pdef_share = float(defense_profile.get("pdef_share", 0.5))
            mdef_share = float(defense_profile.get("mdef_share", 0.5))

            total_defense = int(round(base_total * total_multiplier))

            if total_defense < 2:
                total_defense = 2

            new_pdef = int(round(total_defense * pdef_share))
            new_mdef = int(round(total_defense * mdef_share))

            new_pdef = max(1, new_pdef)
            new_mdef = max(1, new_mdef)

            # Гарантія: тканина завжди має MDEF > PDEF.
            if armor_type == "cloth" and new_mdef <= new_pdef:
                total = max(2, new_pdef + new_mdef)
                new_mdef = max(1, int(round(total * 0.70)))
                new_pdef = max(1, total - new_mdef)

                if new_mdef <= new_pdef:
                    new_mdef = new_pdef + 1

            # Гарантія: лати завжди мають PDEF > MDEF.
            if armor_type == "plate" and new_pdef <= new_mdef:
                total = max(2, new_pdef + new_mdef)
                new_pdef = max(1, int(round(total * 0.88)))
                new_mdef = max(1, total - new_pdef)

                if new_pdef <= new_mdef:
                    new_pdef = new_mdef + 1

            stats["pdef"] = new_pdef
            stats["mdef"] = new_mdef

    # ==============================
    # 2. Primary stats redistribution
    # ==============================

    stats = apply_armor_type_primary_stat_profile_to_stats(
        stats=stats,
        armor_type=armor_type
    )

    return stats

def normalize_dev_rarity(rarity):
    rarity = (rarity or "common").strip().lower()

    aliases = {
        "white": "common",
        "білий": "common",
        "bilyi": "common",

        "green": "uncommon",
        "зелений": "uncommon",
        "zelenyi": "uncommon",

        "blue": "rare",
        "синій": "rare",
        "synii": "rare",

        "purple": "epic",
        "фіолетовий": "epic",
        "fioletovyi": "epic",
    }

    rarity = aliases.get(rarity, rarity)

    if rarity not in ["common", "uncommon", "rare", "epic"]:
        rarity = "common"

    return rarity

def create_dev_armor_item_for_test(user_id, armor_type, slot_key="chest", item_level=None, rarity="common"):
    """
    DEV-функція.
    Створює броню конкретного armor_type незалежно від класу.

    Приклад:
    create_dev_armor_item_for_test(user_id, "plate", "chest", 5, "rare")
    """

    init_dynamic_equipment_system()
    init_weapon_damage_system()
    init_class_equipment_restrictions_system()

    armor_type = normalize_equipment_restriction_value(armor_type)
    rarity = normalize_dev_rarity(rarity)

    if armor_type not in ["cloth", "leather", "chain", "plate"]:
        return {
            "success": False,
            "message": (
                "❌ Невідомий тип броні.\n\n"
                "Доступно:\n"
                "cloth, leather, chain, plate"
            )
        }

    if slot_key not in ARMOR_SLOTS:
        return {
            "success": False,
            "message": (
                "❌ Невідомий слот броні.\n\n"
                "Доступно:\n"
                "helmet, shoulders, chest, gloves, legs, boots"
            )
        }

    if item_level is None:
        item_level = get_player_level(user_id)

    try:
        item_level = int(item_level)
    except Exception:
        item_level = get_player_level(user_id)

    item_level = max(1, item_level)

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена. Предмет не створено."
        }

    item_profile = ""
    weapon_hands = 1
    weapon_attack_type = ""

    base_name = get_dynamic_armor_name(slot_key, rarity)
    armor_label = get_armor_type_label(armor_type)
    name = f"{base_name} [{armor_label}] {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    stats = apply_armor_type_defense_profile_to_stats(
        stats=stats,
        armor_type=armor_type
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    item_id = allocate_generated_item_id(conn)
    cursor.execute("""
    INSERT INTO items (
        id,
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        armor_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_id,
        name,
        slot_key,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1,
        item_profile,
        0,
        0,
        0,
        0,
        weapon_attack_type,
        armor_type
    ))


    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ DEV: броню створено.\n\n"
            f"📦 {name}\n"
            f"🎯 Слот: {EQUIPMENT_SLOTS.get(slot_key, slot_key)}\n"
            f"🧵 Тип броні: {get_armor_type_label(armor_type)}\n"
            f"🏷 Рівень: {item_level}\n"
            f"⭐ Рідкість: {rarity}\n"
            f"🆔 inventory_id: {inventory_id}"
        ),
        "item_id": item_id,
        "inventory_id": inventory_id,
        "armor_type": armor_type,
        "slot_key": slot_key
    }

def create_dev_weapon_item_for_test(user_id, item_profile, item_level=None, rarity="common"):
    """
    DEV-функція.
    Створює зброю або off-hand конкретного item_subtype незалежно від класу.

    Приклади:
    create_dev_weapon_item_for_test(user_id, "dagger_1h", 5, "rare")
    create_dev_weapon_item_for_test(user_id, "shield", 5, "common")
    """

    init_dynamic_equipment_system()
    init_weapon_damage_system()
    init_class_equipment_restrictions_system()

    item_profile = normalize_equipment_restriction_value(item_profile)
    rarity = normalize_dev_rarity(rarity)

    if item_profile in MAIN_HAND_PROFILES:
        slot_key = "main_hand"
        profile = MAIN_HAND_PROFILES[item_profile]
        weapon_hands = profile["hands"]
        weapon_attack_type = profile["attack_type"]
        type_ = "weapon"

    elif item_profile in OFF_HAND_PROFILES:
        slot_key = "off_hand"
        profile = OFF_HAND_PROFILES[item_profile]
        weapon_hands = 1
        weapon_attack_type = profile["attack_type"]
        type_ = "offhand"

    else:
        return {
            "success": False,
            "message": (
                "❌ Невідомий тип зброї / off-hand.\n\n"
                "Main hand:\n"
                "sword_1h, dagger_1h, wand_1h, sword_2h, staff_2h, bow_2h, crossbow_2h\n\n"
                "Off hand:\n"
                "shield, talisman, dagger"
            )
        }

    if item_level is None:
        item_level = get_player_level(user_id)

    try:
        item_level = int(item_level)
    except Exception:
        item_level = get_player_level(user_id)

    item_level = max(1, item_level)

    capacity = get_bag_capacity(user_id)
    used_slots = get_inventory_used_slots(user_id)

    if used_slots >= capacity:
        return {
            "success": False,
            "message": "🎒 Сумка переповнена. Предмет не створено."
        }

    name = get_dynamic_weapon_name(
        slot_key=slot_key,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    name = f"{name} {item_level} рівня"

    stats = generate_dynamic_equipment_stats(
        slot_key=slot_key,
        item_level=item_level,
        rarity=rarity,
        weapon_hands=weapon_hands,
        item_profile=item_profile
    )

    sell_price = get_dynamic_sell_price(item_level, rarity)

    weapon_min_damage = 0
    weapon_max_damage = 0
    weapon_min_magic_damage = 0
    weapon_max_magic_damage = 0

    if slot_key == "main_hand":
        min_dmg, max_dmg = calculate_weapon_damage_by_values(
            item_level=item_level,
            rarity=rarity,
            weapon_hands=weapon_hands
        )

        if weapon_attack_type == "magical":
            weapon_min_magic_damage = min_dmg
            weapon_max_magic_damage = max_dmg
        else:
            weapon_min_damage = min_dmg
            weapon_max_damage = max_dmg

    item_id = allocate_generated_item_id(conn)
    cursor.execute("""
    INSERT INTO items (
        id,
        name,
        type,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        bonus_str,
        bonus_dex,
        bonus_int,
        bonus_wis,
        bonus_sta,
        pdef,
        mdef,
        item_level,
        is_generated,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        armor_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_id,
        name,
        type_,
        rarity,
        "equipment",
        slot_key,
        weapon_hands,
        1,
        sell_price,
        stats["bonus_str"],
        stats["bonus_dex"],
        stats["bonus_int"],
        stats["bonus_wis"],
        stats["bonus_sta"],
        stats["pdef"],
        stats["mdef"],
        item_level,
        1,
        item_profile,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        ""
    ))


    cursor.execute("""
    INSERT INTO inventory (
        user_id,
        item_id,
        quantity,
        durability
    )
    VALUES (?, ?, ?, ?)
    """, (
        user_id,
        item_id,
        1,
        100
    ))

    inventory_id = cursor.lastrowid

    conn.commit()

    return {
        "success": True,
        "message": (
            f"✅ DEV: зброю / off-hand створено.\n\n"
            f"📦 {name}\n"
            f"🎯 Слот: {EQUIPMENT_SLOTS.get(slot_key, slot_key)}\n"
            f"⚔️ Тип предмета: {get_item_subtype_label(item_profile)}\n"
            f"🏷 Рівень: {item_level}\n"
            f"⭐ Рідкість: {rarity}\n"
            f"🆔 inventory_id: {inventory_id}"
        ),
        "item_id": item_id,
        "inventory_id": inventory_id,
        "item_subtype": item_profile,
        "slot_key": slot_key
    }

def _player_system_v1():
    from systems import player_system as _mod
    return _mod

def get_max_hp(user_id):
    return _player_system_v1().get_max_hp(user_id)

def _equipment_system_ro_v1():
    from systems import equipment_system
    return equipment_system

def init_weapon_damage_system(*args, **kwargs):
    return _equipment_system_ro_v1().init_weapon_damage_system(*args, **kwargs)

def calculate_weapon_damage_by_values(*args, **kwargs):
    return _equipment_system_ro_v1().calculate_weapon_damage_by_values(*args, **kwargs)

def _player_system_v2():
    from systems import player_system as _mod
    return _mod

def get_player_level(user_id):
    return _player_system_v2().get_player_level(user_id)

__all__ = ['set_player_level_for_test', 'reset_player_level_for_test', 'set_gold_for_test', 'create_dev_armor_item_for_test', 'create_dev_weapon_item_for_test', 'reset_hero_for_test', 'seed_class_reset_sphere_item']

# Stage 17.14.1.1 DEV-only current-level EXP setter.
def set_current_exp_for_test_17_14_1_1(user_id, requested):
    row = cursor.execute(
        "SELECT level, exp FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return {"success": False, "message": "❌ Персонажа не знайдено."}

    level = max(1, int(row[0] or 1))
    from data.player_progression import get_exp_to_next_level
    required = int(get_exp_to_next_level(level))

    if str(requested).strip().casefold() == "near":
        value = max(0, required - 1)
    else:
        try:
            value = int(str(requested).strip())
        except Exception:
            return {
                "success": False,
                "message": "❌ Формат: /setexp <0..поріг-1> або /setexp near",
            }

    if value < 0 or value >= required:
        return {
            "success": False,
            "message": f"❌ Для {level} рівня EXP має бути в межах 0–{required - 1}.",
            "level": level,
            "required": required,
        }

    cursor.execute("UPDATE users SET exp=? WHERE user_id=?", (value, int(user_id)))
    conn.commit()
    return {
        "success": True,
        "level": level,
        "exp": value,
        "required": required,
        "remaining": required - value,
        "message": (
            "✅ DEV: досвід персонажа встановлено.\n\n"
            f"Рівень: {level}\n"
            f"Досвід: {value}/{required}\n"
            f"До нового рівня: {required - value} EXP"
        ),
    }

