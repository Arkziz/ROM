from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_2d_notification_hp_dynamic_max_fix"
TARGET_RELATIVE = Path("systems") / "notifications.py"
MARKER = "# ✅ ROM 9.0.2d NOTIFICATION HP DYNAMIC MAX FIX V1"

APPEND_CODE = r'''

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
    """
    Calculates HP bonus from currently equipped refined armor for notification worker.

    Current known rule from refine 6.0:
    - armor +6 gives +4% max HP;
    - therefore 1 refine level ~= 0.6667% max HP.

    This mirrors the gameplay intent well enough for notification/full-HP checks.
    """

    try:
        equipment_cols = _worker_table_columns_v1(conn, "equipment_slots")
        inventory_cols = _worker_table_columns_v1(conn, "inventory")
        item_cols = _worker_table_columns_v1(conn, "items")

        if not {"user_id", "slot_key", "inventory_id"}.issubset(equipment_cols):
            return 0.0

        if "refine_level" not in inventory_cols:
            return 0.0

        if "slot_key" not in item_cols:
            return 0.0

        rows = conn.execute("""
        SELECT
            es.slot_key AS equipped_slot,
            COALESCE(inv.refine_level, 0) AS refine_level,
            items.slot_key AS item_slot,
            items.category AS category
        FROM equipment_slots es
        JOIN inventory inv ON inv.id = es.inventory_id
        JOIN items ON items.id = inv.item_id
        WHERE es.user_id=?
          AND es.inventory_id IS NOT NULL
        """, (user_id,)).fetchall()

        total_percent = 0.0

        for row in rows:
            equipped_slot = row[0]
            refine_level = int(row[1] or 0)
            item_slot = row[2]

            slot = equipped_slot or item_slot

            if refine_level <= 0:
                continue

            if slot not in WORKER_ARMOR_SLOTS_FOR_HP_REFINE_V1:
                continue

            total_percent += refine_level * WORKER_ARMOR_HP_BONUS_PER_REFINE_LEVEL_V1

        return max(0.0, total_percent)

    except Exception:
        return 0.0


def get_worker_max_hp(conn, user_id):
    """
    Dynamic max HP for notification worker.

    Uses the existing worker base formula, then applies refine armor HP bonus.
    Also syncs users.max_hp so DB snapshots match profile logic.
    """

    if _notifications_base_get_worker_max_hp_before_dynamic_refine_v1:
        try:
            base_hp = int(_notifications_base_get_worker_max_hp_before_dynamic_refine_v1(conn, user_id) or 1)
        except Exception:
            base_hp = 100
    else:
        base_hp = 100

    bonus_percent = get_worker_armor_refine_hp_bonus_percent_v1(conn, user_id)
    dynamic_max_hp = int(round(base_hp * (1 + bonus_percent / 100.0)))
    dynamic_max_hp = max(1, dynamic_max_hp)

    try:
        user_cols = _worker_table_columns_v1(conn, "users")
        if "max_hp" in user_cols:
            conn.execute(
                "UPDATE users SET max_hp=? WHERE user_id=?",
                (dynamic_max_hp, user_id),
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
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч уже застосовано раніше.")
        return

    backup = make_backup(root, target)

    try:
        target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_9_0_2d_notification_hp_dynamic_max_fix.\n"
            "Файл systems/notifications.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.2d Notification HP dynamic max fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/notifications.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- notification worker тепер враховує HP bonus від заточеної броні")
    print("- повідомлення про повне HP не має приходити на 365/380")
    print("- пасивна HP-регенерація має доводити HP до динамічного максимуму")
    print("- users.max_hp синхронізується з worker dynamic max HP")


if __name__ == "__main__":
    main()
