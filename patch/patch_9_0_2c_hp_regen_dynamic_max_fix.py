from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_2c_hp_regen_dynamic_max_fix"
TARGET_RELATIVE = Path("db.py")
MARKER = "# ✅ ROM 9.0.2c HP REGEN DYNAMIC MAX FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.2c HP REGEN DYNAMIC MAX FIX V1
# ==============================

# Fix reason:
# After refined armor changes max HP dynamically, stored users.max_hp can become stale.
# Legacy passive regen can then reset last_hp_regen_update while hp < dynamic max_hp,
# so HP may stay like 365/380 and not regenerate as expected.

try:
    _legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1 = process_passive_regeneration
except NameError:
    _legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1 = None


def _hp_regen_parse_dt_v1(value):
    from datetime import datetime

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


def _hp_regen_user_columns_v1():
    try:
        cursor.execute("PRAGMA table_info(users)")
        return {row[1] for row in cursor.fetchall()}
    except Exception:
        return set()


def _hp_regen_get_config_v1():
    minutes = globals().get("HP_REGEN_MINUTES", 1)
    percent = globals().get("HP_REGEN_PERCENT", 0.10)

    try:
        minutes = int(minutes)
    except Exception:
        minutes = 1

    try:
        percent = float(percent)
    except Exception:
        percent = 0.10

    if minutes <= 0:
        minutes = 1

    if percent <= 0:
        percent = 0.10

    return minutes, percent


def process_passive_regeneration(user_id):
    """
    Dynamic-max-HP-safe passive regeneration.

    Rules:
    - max HP is always recalculated through get_max_hp(user_id);
    - users.max_hp is synchronized through sync_user_max_hp() if available;
    - if max HP increased because of refined armor, HP is not healed immediately;
    - passive regen then heals toward the new dynamic max HP;
    - last_hp_regen_update is NOT reset when hp < max_hp and no regen tick passed.
    """

    from datetime import datetime

    now = datetime.now()
    now_iso = now.isoformat()

    try:
        # Sync stale users.max_hp with dynamic equipment/refine HP.
        if "sync_user_max_hp" in globals():
            sync_user_max_hp(user_id, heal_to_full=False)
    except Exception:
        pass

    columns = _hp_regen_user_columns_v1()

    select_cols = ["hp"]
    if "max_hp" in columns:
        select_cols.append("max_hp")
    if "last_hp_regen_update" in columns:
        select_cols.append("last_hp_regen_update")
    if "mp" in columns:
        select_cols.append("mp")
    if "max_mp" in columns:
        select_cols.append("max_mp")

    try:
        cursor.execute(
            f"SELECT {', '.join(select_cols)} FROM users WHERE user_id=?",
            (user_id,)
        )
        row = cursor.fetchone()
    except Exception:
        row = None

    if not row:
        # Fallback to legacy if DB shape is unexpected.
        if _legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1:
            return _legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1(user_id)
        return {"success": False, "minutes": 0, "hp_restored": 0, "mp_restored": 0}

    def row_get(key, index, default=None):
        try:
            return row[key]
        except Exception:
            pass
        try:
            return row[index]
        except Exception:
            return default

    idx = {name: i for i, name in enumerate(select_cols)}

    try:
        dynamic_max_hp = int(get_max_hp(user_id) or 1)
    except Exception:
        dynamic_max_hp = int(row_get("max_hp", idx.get("max_hp", 0), 1) or 1)

    current_hp = int(row_get("hp", idx.get("hp", 0), dynamic_max_hp) or 0)

    last_value = None
    if "last_hp_regen_update" in idx:
        last_value = row_get("last_hp_regen_update", idx["last_hp_regen_update"], None)

    last_dt = _hp_regen_parse_dt_v1(last_value)

    # Initialize timestamp only if absent. Do not heal instantly.
    if last_dt is None:
        if "last_hp_regen_update" in columns:
            try:
                cursor.execute(
                    "UPDATE users SET max_hp=?, last_hp_regen_update=? WHERE user_id=?",
                    (dynamic_max_hp, now_iso, user_id)
                )
                conn.commit()
            except Exception:
                pass

        return {"success": True, "minutes": 0, "hp_restored": 0, "mp_restored": 0}

    elapsed_seconds = (now - last_dt).total_seconds()

    if elapsed_seconds < 0:
        elapsed_seconds = 0
        last_dt = now

    elapsed_minutes = int(elapsed_seconds // 60)
    regen_minutes, regen_percent = _hp_regen_get_config_v1()
    ticks = elapsed_minutes // regen_minutes

    hp_restored = 0
    mp_restored = 0
    new_hp = current_hp

    # Only heal if player is below dynamic max HP and a regen tick actually passed.
    if current_hp < dynamic_max_hp and ticks > 0:
        heal_per_tick = max(1, int(round(dynamic_max_hp * regen_percent)))
        hp_restored = min(dynamic_max_hp - current_hp, heal_per_tick * ticks)
        new_hp = min(dynamic_max_hp, current_hp + hp_restored)

        try:
            if "max_hp" in columns and "last_hp_regen_update" in columns:
                cursor.execute(
                    "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? WHERE user_id=?",
                    (new_hp, dynamic_max_hp, now_iso, user_id)
                )
            elif "max_hp" in columns:
                cursor.execute(
                    "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
                    (new_hp, dynamic_max_hp, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET hp=? WHERE user_id=?",
                    (new_hp, user_id)
                )
            conn.commit()
        except Exception:
            pass

    elif current_hp >= dynamic_max_hp:
        # Full or overhealed: keep DB consistent and reset timer to now.
        clamped_hp = min(current_hp, dynamic_max_hp)
        try:
            if "max_hp" in columns and "last_hp_regen_update" in columns:
                cursor.execute(
                    "UPDATE users SET hp=?, max_hp=?, last_hp_regen_update=? WHERE user_id=?",
                    (clamped_hp, dynamic_max_hp, now_iso, user_id)
                )
            elif "max_hp" in columns:
                cursor.execute(
                    "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
                    (clamped_hp, dynamic_max_hp, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET hp=? WHERE user_id=?",
                    (clamped_hp, user_id)
                )
            conn.commit()
        except Exception:
            pass

        new_hp = clamped_hp

    else:
        # Below max but no tick yet: only ensure stored max_hp is correct.
        try:
            if "max_hp" in columns:
                cursor.execute(
                    "UPDATE users SET max_hp=? WHERE user_id=?",
                    (dynamic_max_hp, user_id)
                )
                conn.commit()
        except Exception:
            pass

    return {
        "success": True,
        "minutes": elapsed_minutes,
        "hp_restored": hp_restored,
        "mp_restored": mp_restored,
        "hp": new_hp,
        "max_hp": dynamic_max_hp,
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
            "❌ Помилка компіляції після patch_9_0_2c_hp_regen_dynamic_max_fix.\n"
            "Файл db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.2c HP regen dynamic max fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ db.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- passive HP regen використовує динамічний get_max_hp(user_id)")
    print("- users.max_hp синхронізується перед регенерацією")
    print("- last_hp_regen_update не скидається дарма, коли hp < max_hp і tick ще не минув")
    print("- HP має регенерувати з 365/380 до 380/380")


if __name__ == "__main__":
    main()
