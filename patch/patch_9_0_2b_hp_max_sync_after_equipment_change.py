from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_2b_hp_max_sync_after_equipment_change"
PLAYER_TARGET = Path("systems") / "player_system.py"
DB_TARGET = Path("db.py")
PLAYER_MARKER = "# ✅ ROM 9.0.2b HP MAX SYNC V1"
DB_MARKER = "# ✅ ROM 9.0.2b HP MAX SYNC DB WRAPPER V1"

PLAYER_APPEND = r'''

# ==============================
# ✅ ROM 9.0.2b HP MAX SYNC V1
# ==============================

try:
    _player_system_base_get_current_hp_raw_before_hp_sync_v1 = get_current_hp_raw
except NameError:
    _player_system_base_get_current_hp_raw_before_hp_sync_v1 = None

try:
    _player_system_base_get_current_hp_before_hp_sync_v1 = get_current_hp
except NameError:
    _player_system_base_get_current_hp_before_hp_sync_v1 = None

try:
    _player_system_base_set_current_hp_before_hp_sync_v1 = set_current_hp
except NameError:
    _player_system_base_set_current_hp_before_hp_sync_v1 = None


def sync_user_max_hp(user_id: int, heal_to_full: bool = False):
    """
    Synchronize stored users.max_hp with the real dynamic get_max_hp(user_id).

    Important gameplay rule:
    - Equipping +HP armor raises max HP but does NOT heal missing HP automatically.
    - Removing +HP armor lowers max HP and clamps current HP if it is above new max.

    This fixes stale max_hp in DB, which may cause notification worker to say
    "full HP" using stored max_hp while dynamic max HP from refined armor is higher.
    """

    db = _db_module()
    dynamic_max_hp = int(get_max_hp(user_id) or 1)

    try:
        row = _fetchone("SELECT hp, max_hp FROM users WHERE user_id=?", (user_id,))
    except Exception:
        return {
            "success": False,
            "max_hp": dynamic_max_hp,
            "hp": dynamic_max_hp if heal_to_full else 0,
            "changed": False,
        }

    if not row:
        return {
            "success": False,
            "max_hp": dynamic_max_hp,
            "hp": 0,
            "changed": False,
        }

    current_hp = int(_row_get(row, "hp", 0, dynamic_max_hp) or 0)
    stored_max_hp = int(_row_get(row, "max_hp", 1, dynamic_max_hp) or dynamic_max_hp)

    if heal_to_full:
        new_hp = dynamic_max_hp
    else:
        new_hp = min(current_hp, dynamic_max_hp)

    changed = (stored_max_hp != dynamic_max_hp) or (current_hp != new_hp)

    if changed:
        try:
            _execute_commit(
                "UPDATE users SET hp=?, max_hp=? WHERE user_id=?",
                (new_hp, dynamic_max_hp, user_id),
            )
        except Exception:
            # If max_hp column is absent in some older DB, still try to clamp hp.
            try:
                _execute_commit(
                    "UPDATE users SET hp=? WHERE user_id=?",
                    (new_hp, user_id),
                )
            except Exception:
                pass

    return {
        "success": True,
        "hp": new_hp,
        "max_hp": dynamic_max_hp,
        "old_hp": current_hp,
        "old_max_hp": stored_max_hp,
        "changed": changed,
    }


def get_current_hp_raw(user_id: int):
    sync = sync_user_max_hp(user_id, heal_to_full=False)

    if sync.get("success"):
        return int(sync.get("hp", 0) or 0)

    if _player_system_base_get_current_hp_raw_before_hp_sync_v1:
        return _player_system_base_get_current_hp_raw_before_hp_sync_v1(user_id)

    row = _fetchone("SELECT hp FROM users WHERE user_id=?", (user_id,))
    return int(_row_get(row, "hp", 0, get_max_hp(user_id)) or get_max_hp(user_id))


def get_current_hp(user_id: int):
    sync = sync_user_max_hp(user_id, heal_to_full=False)

    if sync.get("success"):
        return int(sync.get("hp", 0) or 0)

    if _player_system_base_get_current_hp_before_hp_sync_v1:
        return _player_system_base_get_current_hp_before_hp_sync_v1(user_id)

    return get_current_hp_raw(user_id)


def set_current_hp(user_id: int, hp: int):
    sync = sync_user_max_hp(user_id, heal_to_full=False)
    max_hp = int(sync.get("max_hp", get_max_hp(user_id)) or get_max_hp(user_id))
    safe_hp = max(0, min(int(hp), max_hp))

    try:
        _execute_commit("UPDATE users SET hp=?, max_hp=? WHERE user_id=?", (safe_hp, max_hp, user_id))
        return safe_hp
    except Exception:
        if _player_system_base_set_current_hp_before_hp_sync_v1:
            return _player_system_base_set_current_hp_before_hp_sync_v1(user_id, safe_hp)
        return safe_hp
'''

DB_APPEND = r'''

# ==============================
# ✅ ROM 9.0.2b HP MAX SYNC DB WRAPPER V1
# ==============================


def sync_user_max_hp(user_id, heal_to_full=False):
    from systems import player_system as _mod
    return _mod.sync_user_max_hp(user_id, heal_to_full=heal_to_full)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_once(root, rel_path, marker, append_code):
    target = root / rel_path

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if marker in original:
        return target, None, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + append_code + "\n", encoding="utf-8")
    return target, backup, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed = []
    backups = []
    originals = []

    try:
        for rel_path, marker, code in [
            (PLAYER_TARGET, PLAYER_MARKER, PLAYER_APPEND),
            (DB_TARGET, DB_MARKER, DB_APPEND),
        ]:
            target = root / rel_path
            original = target.read_text(encoding="utf-8") if target.exists() else None
            path, backup, did_change = append_once(root, rel_path, marker, code)
            if did_change:
                changed.append(path)
                originals.append((path, original))
            if backup:
                backups.append(backup)

        py_compile.compile(str(root / PLAYER_TARGET), doraise=True)
        py_compile.compile(str(root / DB_TARGET), doraise=True)

    except Exception as error:
        for path, original in originals:
            if original is not None:
                try:
                    path.write_text(original, encoding="utf-8")
                except Exception:
                    pass

        raise SystemExit(
            "❌ Помилка під час patch_9_0_2b_hp_max_sync_after_equipment_change.\n"
            "Файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.2b HP max sync застосовано успішно.")

    if changed:
        print("\nЗмінено:")
        for path in changed:
            print(f"- {path}")

    if backups:
        print("\nBackup:")
        for path in backups:
            print(f"- {path}")

    print("\nЩо виправлено:")
    print("- додано sync_user_max_hp(user_id, heal_to_full=False)")
    print("- users.max_hp синхронізується з динамічним get_max_hp(user_id)")
    print("- при зменшенні max HP поточне HP обрізається до нового максимуму")
    print("- при збільшенні max HP персонаж НЕ лікується автоматично")
    print("- get_current_hp/get_current_hp_raw тепер повертають консистентне HP")

    print("\nПісля патча запусти:")
    print("python -m py_compile .\\systems\\player_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python -c \"import db; uid=243129101; print(db.sync_user_max_hp(uid)); print(db.get_current_hp(uid), db.get_max_hp(uid))\"")


if __name__ == "__main__":
    main()
