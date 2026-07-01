import time
import threading
import sqlite3
from datetime import datetime, timedelta


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
        ("users", "energy", "INTEGER DEFAULT 40"),
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
    WHERE energy IS NULL OR energy > ?
    """, (ENERGY_MAX, ENERGY_MAX))

    conn.commit()


def apply_energy_regen(conn, user_id):
    """
    Повертає актуальну енергію з урахуванням регенерації.
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
        energy = ENERGY_MAX

    now = datetime.now()

    if not last_update:
        last_update_dt = now
    else:
        try:
            last_update_dt = datetime.fromisoformat(last_update)
        except Exception:
            last_update_dt = now

    if energy < ENERGY_MAX:
        diff_seconds = (now - last_update_dt).total_seconds()
        regen_units = int(diff_seconds // (ENERGY_REGEN_MINUTES * 60))

        if regen_units > 0:
            energy = min(ENERGY_MAX, energy + regen_units)
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

    else:
        energy = ENERGY_MAX

        conn.execute("""
        UPDATE users
        SET energy=?,
            last_energy_update=?
        WHERE user_id=?
        """, (
            ENERGY_MAX,
            now.isoformat(),
            user_id
        ))

        conn.commit()

    return {
        "energy": energy,
        "max_energy": ENERGY_MAX
    }


def get_users_for_energy_full_notification_worker(conn):
    """
    Повертає user_id гравців, у яких енергія стала повною,
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

        if energy >= max_energy and not notified:
            notify_users.append(user_id)

            conn.execute("""
            UPDATE users
            SET energy_full_notified=1
            WHERE user_id=?
            """, (user_id,))

        elif energy < max_energy and notified:
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


def get_worker_max_hp(conn, user_id):
    """
    Повторює логіку get_max_hp з db.py:
    max_hp = 100 + level * 20 + total_sta * 5
    """

    row = conn.execute("""
    SELECT level, sta
    FROM users
    WHERE user_id=?
    """, (user_id,)).fetchone()

    if not row:
        return 100

    level, base_sta = row

    level = level or 1
    base_sta = base_sta or 10

    item_sta = get_equipped_stat_bonus(conn, user_id, "bonus_sta")

    total_sta = base_sta + item_sta

    return 100 + (level * 20) + (total_sta * 5)


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
                    "🔋 Енергія повністю відновлена!\n\n"
                    "Ти знову маєш повний запас енергії.\n"
                    "Можна вирушати на полювання."
                )
            )
        except Exception as send_error:
            print(f"⚠️ Не вдалося надіслати energy notification {user_id}: {send_error}")


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
            print(f"⚠️ Не вдалося надіслати HP notification {user_id}: {send_error}")


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

    print("✅ NOTIFICATION WORKER DB CONNECTION READY")

    while True:
        try:
            notify_energy_full(bot_instance, conn)
            notify_hp_restored(bot_instance, conn)

            # Майбутні повідомлення:
            # notify_daily_contracts_reset(bot_instance, conn)
            # notify_craft_or_repair_ready(bot_instance, conn)

        except Exception as error:
            print(f"⚠️ NOTIFICATION WORKER ERROR: {error}")

            try:
                conn.close()
            except Exception:
                pass

            try:
                conn = create_worker_connection()
                print("✅ NOTIFICATION WORKER DB CONNECTION RECREATED")
            except Exception as reconnect_error:
                print(f"❌ NOTIFICATION WORKER DB RECONNECT ERROR: {reconnect_error}")

        time.sleep(NOTIFICATION_CHECK_INTERVAL_SECONDS)


def start_notification_worker(bot_instance):
    thread = threading.Thread(
        target=notification_worker,
        args=(bot_instance,),
        daemon=True
    )

    thread.start()

    print("✅ NOTIFICATION WORKER STARTED")