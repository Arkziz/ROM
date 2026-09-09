
# ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY
from systems.production_logging import get_production_logger, production_log_print as PRODUCTION_LOG_PRINT
from data.player_hp import calculate_base_max_hp, get_starting_max_hp
PRODUCTION_LOGGER=get_production_logger('systems.notifications')
# ROM 17.15.1.1 NOTIFICATION WORKER DYNAMIC RUNE MAX MP RECOVERY
# ROM 17.15.1 PERSISTENT MANA REGENERATION
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from systems.inactivity_reminder_system import process_inactivity_reminders, INACTIVITY_SCAN_INTERVAL_SECONDS

_INACTIVITY_REMINDER_NEXT_SCAN_MONOTONIC = 0.0


# ==============================
# ✅ NOTIFICATION CONFIG
# ==============================

DB_PATH = "game.db"

NOTIFICATION_CHECK_INTERVAL_SECONDS = 60

ENERGY_MAX = 40
ENERGY_REGEN_MINUTES = 5

HP_REGEN_PERCENT = 0.10
HP_REGEN_MINUTES = 1


# ==============================
# ✅ DB CONNECTION FOR WORKER
# ==============================

def create_worker_connection():
    """
    Окреме SQLite-підключення для notification worker.
    Не використовує глобальний conn/cursor з db.py.
    """

    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30
    )

    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass

    return conn


# ==============================
# ✅ ENERGY HELPERS
# ==============================

def init_energy_columns(conn):
    migrations = [
        ("users", "energy", "INTEGER DEFAULT 0"),
        ("users", "last_energy_update", "TEXT DEFAULT ''"),
        ("users", "energy_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.execute("""
    UPDATE users
    SET energy = ?
    WHERE energy IS NULL OR energy < 0
    """, (0,))

    # Видалено небезпечне обнулення - це спричиняло помилки при регенерації energ


def apply_energy_regen(conn, user_id):
    """
    Повертає актуальну Втому з урахуванням зниження (регенації).
    """

    init_energy_columns(conn)

    row = conn.execute("""
    SELECT energy, last_energy_update
    FROM users
    WHERE user_id=?
    """, (user_id,)).fetchone()

    if not row:
        return {
            "energy": 0,
            "max_energy": ENERGY_MAX
        }

    energy, last_update = row

    if energy is None:
        energy = 0

    now = datetime.now()

    if not last_update:
        last_update_dt = now
    else:
        try:
            last_update_dt = datetime.fromisoformat(last_update)
        except Exception:
            last_update_dt = now

    if energy > 0:
        diff_seconds = (now - last_update_dt).total_seconds()
        regen_units = int(diff_seconds // (ENERGY_REGEN_MINUTES * 60))

        if regen_units > 0:
            energy = max(0, energy - regen_units)
            last_update_dt = last_update_dt + timedelta(
                minutes=regen_units * ENERGY_REGEN_MINUTES
            )

            conn.execute("""
            UPDATE users
            SET energy=?,
                last_energy_update=?
            WHERE user_id=?
            """, (
                energy,
                last_update_dt.isoformat(),
                user_id
            ))

            conn.commit()

    # Коли energy == 0, не потрібно оновлювати таймер (він вже на 0)

    return {
        "energy": energy,
        "max_energy": ENERGY_MAX
    }


def get_users_for_energy_full_notification_worker(conn):
    """
    Повертає user_id гравців, у яких Втома стала 0 (повністю відновлено),
    але повідомлення ще не надсилалося.
    """

    init_energy_columns(conn)

    rows = conn.execute("""
    SELECT user_id
    FROM users
    """).fetchall()

    notify_users = []

    for row in rows:
        user_id = row[0]

        energy_data = apply_energy_regen(conn, user_id)
        energy = energy_data["energy"]
        max_energy = energy_data["max_energy"]

        notified_row = conn.execute("""
        SELECT energy_full_notified
        FROM users
        WHERE user_id=?
        """, (user_id,)).fetchone()

        notified = notified_row[0] if notified_row else 0

        if energy <= 0 and not notified:
            notify_users.append(user_id)

            conn.execute("""
            UPDATE users
            SET energy_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif energy > 0 and notified:
            conn.execute("""
            UPDATE users
            SET energy_full_notified=0
            WHERE user_id=?
            """, (user_id,))

    conn.commit()

    return notify_users


# ==============================
# ✅ HP HELPERS
# ==============================

def init_hp_columns(conn):
    migrations = [
        ("users", "last_hp_regen_update", "TEXT DEFAULT ''"),
        ("users", "hp_full_notified", "INTEGER DEFAULT 1"),
    ]

    for table, column, column_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        except Exception:
            pass

    conn.commit()


def get_equipped_stat_bonus(conn, user_id, stat_column):
    """
    Повертає сумарний бонус екіпірування для конкретної характеристики.
    Враховує тільки вдягнені предмети з durability > 0.
    """

    try:
        rows = conn.execute(f"""
        SELECT items.{stat_column}, inventory.durability
        FROM equipment_slots
        JOIN inventory ON equipment_slots.inventory_id = inventory.id
        JOIN items ON inventory.item_id = items.id
        WHERE equipment_slots.user_id=?
          AND equipment_slots.inventory_id IS NOT NULL
        """, (user_id,)).fetchall()
    except Exception:
        return 0

    total = 0

    for bonus, durability in rows:
        if durability is not None and durability <= 0:
            continue

        total += bonus or 0

    return total





def apply_hp_regen(conn, user_id):
    """
    Повертає актуальне HP з урахуванням пасивної регенерації.
    """

    init_hp_columns(conn)

    row = conn.execute("""
    SELECT hp, last_hp_regen_update
    FROM users
    WHERE user_id=?
    """, (user_id,)).fetchone()

    if not row:
        return {
            "hp": 0,
            "max_hp": 100
        }

    hp, last_update = row
    max_hp = get_worker_max_hp(conn, user_id)

    if hp is None:
        hp = max_hp

    now = datetime.now()

    if not last_update:
        last_update_dt = now

        conn.execute("""
        UPDATE users
        SET last_hp_regen_update=?
        WHERE user_id=?
        """, (
            last_update_dt.isoformat(),
            user_id
        ))

        conn.commit()

        return {
            "hp": hp,
            "max_hp": max_hp
        }

    try:
        last_update_dt = datetime.fromisoformat(last_update)
    except Exception:
        last_update_dt = now

    if hp >= max_hp:
        hp = max_hp

        conn.execute("""
        UPDATE users
        SET hp=?,
            last_hp_regen_update=?,
            hp_full_notified=1
        WHERE user_id=?
        """, (
            max_hp,
            now.isoformat(),
            user_id
        ))

        conn.commit()

        return {
            "hp": max_hp,
            "max_hp": max_hp
        }

    diff_seconds = (now - last_update_dt).total_seconds()
    regen_ticks = int(diff_seconds // (HP_REGEN_MINUTES * 60))

    if regen_ticks <= 0:
        return {
            "hp": hp,
            "max_hp": max_hp
        }

    heal_per_tick = max(1, int(max_hp * HP_REGEN_PERCENT))
    total_heal = heal_per_tick * regen_ticks

    new_hp = min(max_hp, hp + total_heal)

    new_update_dt = last_update_dt + timedelta(
        minutes=regen_ticks * HP_REGEN_MINUTES
    )

    hp_full_notified = 0 if new_hp >= max_hp else 0

    conn.execute("""
    UPDATE users
    SET hp=?,
        last_hp_regen_update=?,
        hp_full_notified=?
    WHERE user_id=?
    """, (
        new_hp,
        new_update_dt.isoformat(),
        hp_full_notified,
        user_id
    ))

    conn.commit()

    return {
        "hp": new_hp,
        "max_hp": max_hp
    }


def get_users_for_hp_full_notification_worker(conn):
    """
    Повертає user_id гравців, у яких HP стало повним,
    але повідомлення ще не надсилалося.
    """

    init_hp_columns(conn)

    rows = conn.execute("""
    SELECT user_id
    FROM users
    """).fetchall()

    notify_users = []

    for row in rows:
        user_id = row[0]

        hp_data = apply_hp_regen(conn, user_id)
        hp = hp_data["hp"]
        max_hp = hp_data["max_hp"]

        notified_row = conn.execute("""
        SELECT hp_full_notified
        FROM users
        WHERE user_id=?
        """, (user_id,)).fetchone()

        notified = notified_row[0] if notified_row else 1

        if hp >= max_hp and not notified:
            notify_users.append(user_id)

            conn.execute("""
            UPDATE users
            SET hp_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif hp < max_hp and notified:
            conn.execute("""
            UPDATE users
            SET hp_full_notified=0
            WHERE user_id=?
            """, (user_id,))

    conn.commit()

    return notify_users


# ==============================
# 🔋 ENERGY NOTIFICATIONS
# ==============================

def notify_energy_full(bot_instance, conn):
    users = get_users_for_energy_full_notification_worker(conn)

    for user_id in users:
        try:
            bot_instance.send_message(
                user_id,
                (
                    "😴 Втома повністю пройшла!\n\n"
                    "Ти знову повний сил.\n"
                    "Можна вирушати на полювання."
                )
            )
        except Exception as send_error:
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Не вдалося надіслати energy notification {user_id}: {send_error}")


# ==============================
# ❤️ HP NOTIFICATIONS
# ==============================

def notify_hp_restored(bot_instance, conn):
    users = get_users_for_hp_full_notification_worker(conn)

    for user_id in users:
        try:
            bot_instance.send_message(
                user_id,
                (
                    "❤️ Здоров’я повністю відновлено!\n\n"
                    "Персонаж готовий до нового полювання."
                )
            )
        except Exception as send_error:
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Не вдалося надіслати HP notification {user_id}: {send_error}")


# ==============================
# 📜 FUTURE CONTRACT NOTIFICATIONS
# ==============================

def notify_daily_contracts_reset(bot_instance, conn):
    pass


# ==============================
# ⚒️ FUTURE CRAFT / REPAIR NOTIFICATIONS
# ==============================

def notify_craft_or_repair_ready(bot_instance, conn):
    pass


# ==============================
# ✅ MAIN NOTIFICATION WORKER
# ==============================

def notification_worker(bot_instance):
    conn = create_worker_connection()

    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', "✅ NOTIFICATION WORKER DB CONNECTION READY")

    while True:
        try:
            notify_energy_full(bot_instance, conn)
            notify_hp_restored(bot_instance, conn)
            notify_mp_restored_17_15_1(bot_instance, conn)

            global _INACTIVITY_REMINDER_NEXT_SCAN_MONOTONIC
            _now_monotonic = time.monotonic()
            if _now_monotonic >= _INACTIVITY_REMINDER_NEXT_SCAN_MONOTONIC:
                _result = process_inactivity_reminders(bot_instance)
                _INACTIVITY_REMINDER_NEXT_SCAN_MONOTONIC = _now_monotonic + INACTIVITY_SCAN_INTERVAL_SECONDS
                if any(_result.values()):
                    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', f"INACTIVITY REMINDER SCAN: {_result}")

            # Майбутні повідомлення:
            # notify_daily_contracts_reset(bot_instance, conn)
            # notify_craft_or_repair_ready(bot_instance, conn)

        except Exception as error:
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ NOTIFICATION WORKER ERROR: {error}")

            try:
                conn.close()
            except Exception:
                pass

            try:
                conn = create_worker_connection()
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', "✅ NOTIFICATION WORKER DB CONNECTION RECREATED")
            except Exception as reconnect_error:
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'error', f"❌ NOTIFICATION WORKER DB RECONNECT ERROR: {reconnect_error}")

        time.sleep(NOTIFICATION_CHECK_INTERVAL_SECONDS)


def start_notification_worker(bot_instance):
    thread = threading.Thread(
        target=notification_worker,
        args=(bot_instance,),
        daemon=True
    )

    thread.start()

    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', "✅ NOTIFICATION WORKER STARTED")


# ==============================
# ✅ ROM 9.0.2d NOTIFICATION HP DYNAMIC MAX FIX V1
# ==============================

# Fix reason:
# Notification worker had its own get_worker_max_hp() formula and did not include
# refine armor HP bonus. Because of that it could treat 365/365 as full HP while
# the real dynamic max HP from +6 armor was 380.
#
# This override keeps notifications worker self-contained and uses the worker DB
# connection instead of importing db.py in the worker thread.

try:
    _notifications_base_get_worker_max_hp_before_dynamic_refine_v1 = get_worker_max_hp
except NameError:
    _notifications_base_get_worker_max_hp_before_dynamic_refine_v1 = None

try:
    _notifications_base_apply_hp_regen_before_dynamic_refine_v1 = apply_hp_regen
except NameError:
    _notifications_base_apply_hp_regen_before_dynamic_refine_v1 = None


WORKER_ARMOR_HP_BONUS_PER_REFINE_LEVEL_V1 = 4.0 / 6.0
WORKER_ARMOR_SLOTS_FOR_HP_REFINE_V1 = {
    "helmet",
    "shoulders",
    "chest",
    "gloves",
    "legs",
    "boots",
}


def _worker_table_columns_v1(conn, table_name):
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}
    except Exception:
        return set()


def _worker_iso_to_dt_v1(value):
    if not value:
        return None

    text = str(value).strip()

    try:
        return datetime.fromisoformat(text.replace("Z", ""))
    except Exception:
        pass

    try:
        return datetime.fromisoformat(text.replace("T", " ").split(".")[0])
    except Exception:
        return None


def get_worker_armor_refine_hp_bonus_percent_v1(conn, user_id):
    """Mirror the canonical armor-refine HP table, including rarity multipliers."""
    base_by_level = {0: 0.0, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.0, 5: 3.0, 6: 4.0}
    rarity_multiplier = {"common": 1.0, "uncommon": 1.1, "rare": 1.2, "epic": 1.3}
    try:
        rows = conn.execute(
            """
            SELECT COALESCE(es.slot_key, items.slot_key),
                   COALESCE(inv.refine_level, 0),
                   LOWER(COALESCE(items.rarity, 'common')),
                   COALESCE(inv.durability, 100)
            FROM equipment_slots es
            JOIN inventory inv
              ON inv.id=es.inventory_id AND inv.user_id=es.user_id
            JOIN items ON items.id=inv.item_id
            WHERE es.user_id=? AND es.inventory_id IS NOT NULL
            """,
            (int(user_id),),
        ).fetchall()
    except Exception:
        return 0.0

    total = 0.0
    for slot_key, refine_level, rarity, durability in rows:
        if str(slot_key or "") not in WORKER_ARMOR_SLOTS_FOR_HP_REFINE_V1:
            continue
        if int(durability or 0) <= 0:
            continue
        try:
            level = max(0, min(6, int(refine_level or 0)))
        except Exception:
            level = 0
        rarity_key = str(rarity or "common").strip().lower()
        total += round(
            base_by_level.get(level, 0.0) * rarity_multiplier.get(rarity_key, 1.0),
            2,
        )
    return round(max(0.0, total), 4)



def get_worker_equipped_rune_sta_bonus_v2(conn, user_id):
    """Return active STA rune levels from equipped, non-broken inventory items."""
    try:
        tables = {str(row[0]) for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        if "inventory_runes" not in tables:
            return 0
        row = conn.execute(
            """
            SELECT COALESCE(SUM(COALESCE(ir.rune_level, 0)), 0)
            FROM equipment_slots es
            JOIN inventory inv
              ON inv.id=es.inventory_id AND inv.user_id=es.user_id
            JOIN inventory_runes ir ON ir.inventory_id=inv.id
            WHERE es.user_id=?
              AND es.inventory_id IS NOT NULL
              AND COALESCE(inv.durability, 100) > 0
              AND LOWER(COALESCE(ir.rune_stat, ''))='sta'
            """,
            (int(user_id),),
        ).fetchone()
        return max(0, int((row[0] if row else 0) or 0))
    except Exception:
        return 0


def get_worker_max_hp(conn, user_id):
    """Calculate worker max HP from the shared canonical HP policy."""
    row = conn.execute(
        "SELECT level, sta FROM users WHERE user_id=?",
        (user_id,),
    ).fetchone()
    if not row:
        return get_starting_max_hp()
    level = int(row[0] or 1)
    base_sta = int(row[1] or 10)
    item_sta = int(get_equipped_stat_bonus(conn, user_id, "bonus_sta") or 0)
    rune_sta = int(get_worker_equipped_rune_sta_bonus_v2(conn, user_id) or 0)
    total_sta = base_sta + item_sta + rune_sta
    base_hp = calculate_base_max_hp(level, total_sta)
    bonus_percent = get_worker_armor_refine_hp_bonus_percent_v1(conn, user_id)
    dynamic_max_hp = max(1, int(round(base_hp * (1 + bonus_percent / 100.0))))
    try:
        user_cols = _worker_table_columns_v1(conn, "users")
        if "max_hp" in user_cols:
            current_row = conn.execute("SELECT hp FROM users WHERE user_id=?", (user_id,)).fetchone()
            current_hp = int(current_row[0] or 0) if current_row else 0
            clamped_hp = min(current_hp, dynamic_max_hp)
            conn.execute(
                "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
                (clamped_hp, dynamic_max_hp, user_id),
            )
            conn.commit()
    except Exception:
        pass
    return dynamic_max_hp


def apply_hp_regen(conn, user_id):
    """
    HP regen that respects dynamic max HP from refined armor.

    Important behavior:
    - equipping refined armor increases max HP but does not heal instantly;
    - passive regen heals toward the dynamic max;
    - full HP notification only fires at dynamic max, not stale stored max_hp.
    """

    init_hp_columns(conn)

    user_cols = _worker_table_columns_v1(conn, "users")
    has_max_hp = "max_hp" in user_cols

    select_cols = ["hp", "last_hp_regen_update"]
    if has_max_hp:
        select_cols.insert(1, "max_hp")

    row = conn.execute(
        f"SELECT {', '.join(select_cols)} FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if not row:
        return {
            "hp": 0,
            "max_hp": 100,
        }

    if has_max_hp:
        hp = row[0]
        stored_max_hp = row[1]
        last_update = row[2]
    else:
        hp = row[0]
        stored_max_hp = None
        last_update = row[1]

    max_hp = get_worker_max_hp(conn, user_id)

    if hp is None:
        hp = max_hp

    hp = int(hp or 0)

    now = datetime.now()

    last_update_dt = _worker_iso_to_dt_v1(last_update)

    if last_update_dt is None:
        conn.execute("""
        UPDATE users
        SET last_hp_regen_update=?
        WHERE user_id=?
        """, (
            now.isoformat(),
            user_id,
        ))
        conn.commit()

        return {
            "hp": min(hp, max_hp),
            "max_hp": max_hp,
        }

    # Clamp overheal / stale HP down to dynamic max.
    if hp >= max_hp:
        hp = max_hp

        conn.execute("""
        UPDATE users
        SET hp=?,
            last_hp_regen_update=?,
            hp_full_notified=1
        WHERE user_id=?
        """, (
            max_hp,
            now.isoformat(),
            user_id,
        ))
        conn.commit()

        return {
            "hp": max_hp,
            "max_hp": max_hp,
        }

    diff_seconds = (now - last_update_dt).total_seconds()

    if diff_seconds < 0:
        diff_seconds = 0

    regen_ticks = int(diff_seconds // (HP_REGEN_MINUTES * 60))

    if regen_ticks <= 0:
        # Below dynamic max but not enough time has passed. Do not mark full.
        if has_max_hp and stored_max_hp != max_hp:
            try:
                conn.execute(
                    "UPDATE users SET max_hp=?, hp_full_notified=0 WHERE user_id=?",
                    (max_hp, user_id),
                )
                conn.commit()
            except Exception:
                pass

        return {
            "hp": hp,
            "max_hp": max_hp,
        }

    heal_per_tick = max(1, int(max_hp * HP_REGEN_PERCENT))
    total_heal = heal_per_tick * regen_ticks
    new_hp = min(max_hp, hp + total_heal)

    new_update_dt = last_update_dt + timedelta(
        minutes=regen_ticks * HP_REGEN_MINUTES
    )

    # If HP became full, keep hp_full_notified=0 so get_users_for_hp_full_notification_worker()
    # can send one notification and then mark it as notified.
    hp_full_notified = 0

    conn.execute("""
    UPDATE users
    SET hp=?,
        max_hp=?,
        last_hp_regen_update=?,
        hp_full_notified=?
    WHERE user_id=?
    """, (
        new_hp,
        max_hp,
        new_update_dt.isoformat(),
        hp_full_notified,
        user_id,
    ))

    conn.commit()

    return {
        "hp": new_hp,
        "max_hp": max_hp,
    }

# Stage 17.15.1 worker-side persistent MP regeneration.
MP_REGEN_PERCENT_PER_MINUTE_17_15_1 = 0.30


def init_mp_columns_worker_17_15_1(conn):
    columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    additions = {
        "last_mp_regen_update": "TEXT DEFAULT ''",
        "mp_full_notified": "INTEGER DEFAULT 1",
        "mp_regen_paused": "INTEGER DEFAULT 0",
    }
    for name, declaration in additions.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE users ADD COLUMN {name} {declaration}")
    conn.commit()


def get_worker_max_mp_17_15_1(conn, user_id):
    row = conn.execute(
        "SELECT level, intelligence, wis, character_class FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row or str(row[3] or "") not in ("mage", "priest"):
        return 0
    level, intelligence, wisdom = (int(row[0] or 0), int(row[1] or 0), int(row[2] or 0))
    return max(0, 100 + level * 20 + intelligence * 3 + wisdom * 2)


def apply_mp_regen_worker_17_15_1(conn, user_id, now=None):
    init_mp_columns_worker_17_15_1(conn)
    maximum = get_worker_max_mp_17_15_1(conn, user_id)
    if maximum <= 0:
        return {"mp": 0, "max_mp": 0, "became_full": False}
    row = conn.execute(
        "SELECT mp,last_mp_regen_update,COALESCE(mp_regen_paused,0) FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return {"mp": 0, "max_mp": maximum, "became_full": False}
    current = max(0, min(int(row[0] or 0), maximum))
    current_time = now or datetime.now()
    try:
        last = datetime.fromisoformat(str(row[1] or ""))
    except Exception:
        last = current_time
    if int(row[2] or 0):
        return {"mp": current, "max_mp": maximum, "became_full": False}
    ticks = max(0, int((current_time-last).total_seconds()//60))
    new_mp = current
    new_stamp = last
    if ticks > 0 and current < maximum:
        new_mp = min(maximum, current + max(1, int(maximum*MP_REGEN_PERCENT_PER_MINUTE_17_15_1))*ticks)
        new_stamp = datetime.fromtimestamp(last.timestamp()+ticks*60)
    conn.execute(
        "UPDATE users SET mp=?,max_mp=?,last_mp_regen_update=?,mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE mp_full_notified END WHERE user_id=?",
        (new_mp,maximum,new_stamp.isoformat(),new_mp,maximum,int(user_id)),
    )
    conn.commit()
    return {"mp":new_mp,"max_mp":maximum,"became_full":current<maximum and new_mp>=maximum}


def get_users_for_mp_full_notification_worker_17_15_1(conn):
    init_mp_columns_worker_17_15_1(conn)
    candidates=[]
    for (user_id,) in conn.execute("SELECT user_id FROM users").fetchall():
        data=apply_mp_regen_worker_17_15_1(conn,user_id)
        if data["max_mp"]<=0 or data["mp"]<data["max_mp"]:
            continue
        row=conn.execute("SELECT COALESCE(mp_full_notified,1) FROM users WHERE user_id=?",(user_id,)).fetchone()
        if row and not int(row[0] or 0):
            candidates.append(int(user_id))
    return candidates


def notify_mp_restored_17_15_1(bot_instance, conn):
    for user_id in get_users_for_mp_full_notification_worker_17_15_1(conn):
        try:
            bot_instance.send_message(
                user_id,
                "🔵 Мана повністю відновлена!\n\nПерсонаж готовий використовувати всі магічні здібності.",
            )
            conn.execute("UPDATE users SET mp_full_notified=1 WHERE user_id=?", (user_id,))
            conn.commit()
        except Exception as send_error:
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Не вдалося надіслати MP notification {user_id}: {send_error}")

# Stage 17.15.1.1: match notification-worker max MP to production rune-aware logic.
def get_worker_equipped_rune_int_wis_bonus_17_15_1_1(conn, user_id):
    """Return active INT/WIS rune levels from equipped, non-broken items."""
    try:
        tables = {str(row[0]) for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        required = {"equipment_slots", "inventory", "inventory_runes"}
        if not required.issubset(tables):
            return {"int": 0, "wis": 0}
        rows = conn.execute(
            """
            SELECT LOWER(COALESCE(ir.rune_stat, '')),
                   COALESCE(SUM(COALESCE(ir.rune_level, 0)), 0)
            FROM equipment_slots es
            JOIN inventory inv
              ON inv.id=es.inventory_id AND inv.user_id=es.user_id
            JOIN inventory_runes ir ON ir.inventory_id=inv.id
            WHERE es.user_id=?
              AND es.inventory_id IS NOT NULL
              AND COALESCE(inv.durability, 100) > 0
              AND LOWER(COALESCE(ir.rune_stat, '')) IN ('int', 'wis')
            GROUP BY LOWER(COALESCE(ir.rune_stat, ''))
            """,
            (int(user_id),),
        ).fetchall()
        result = {"int": 0, "wis": 0}
        for stat, amount in rows:
            if stat in result:
                result[stat] = max(0, int(amount or 0))
        return result
    except Exception:
        return {"int": 0, "wis": 0}


def get_worker_equipped_int_wis_totals_18_15_8c(conn, user_id, base_intelligence, base_wisdom):
    """Reconstruct active item+rune INT/WIS exactly once for the worker."""
    intelligence = int(base_intelligence or 0)
    wisdom = int(base_wisdom or 0)
    try:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(COALESCE(it.bonus_int, 0)), 0),
                COALESCE(SUM(COALESCE(it.bonus_wis, 0)), 0)
            FROM equipment_slots es
            JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id
            JOIN items it ON it.id=inv.item_id
            WHERE es.user_id=? AND es.inventory_id IS NOT NULL
              AND COALESCE(inv.durability, 100) > 0
            """,
            (int(user_id),),
        ).fetchone()
        if row:
            intelligence += int(row[0] or 0)
            wisdom += int(row[1] or 0)
    except Exception:
        pass
    rune = get_worker_equipped_rune_int_wis_bonus_17_15_1_1(conn, user_id)
    intelligence += int(rune.get("int", 0) or 0)
    wisdom += int(rune.get("wis", 0) or 0)
    return intelligence, wisdom

def get_worker_max_mp_17_15_1(conn, user_id):
    """Worker Max MP parity with foreground effective-stat aggregation."""
    row = conn.execute(
        "SELECT level, intelligence, wis, character_class FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    class_key = str(row[3] or "").strip().lower() if row else ""
    if not row or class_key not in ("mage", "priest"):
        return 0
    intelligence, wisdom = get_worker_equipped_int_wis_totals_18_15_8c(
        conn, user_id, row[1], row[2]
    )
    from systems.stat_system import calculate_max_mp
    dynamic_max_mp = calculate_max_mp(
        class_key,
        level=int(row[0] or 0),
        intelligence=intelligence,
        wisdom=wisdom,
    )
    try:
        conn.execute("UPDATE users SET max_mp=? WHERE user_id=?", (dynamic_max_mp, int(user_id)))
        conn.commit()
    except Exception:
        pass
    return dynamic_max_mp

