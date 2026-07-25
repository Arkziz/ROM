from pathlib import Path
from datetime import datetime
import py_compile
import subprocess
import sys

PATCH_NAME = "9_0_12b_character_system_real_implementation"
MARKER = "# ROM 9.0.12b CHARACTER SYSTEM REAL IMPLEMENTATION V1"
OLD_MARKER = "# ✅ ROM 9.0.1 CHARACTER SYSTEM FACADE WRAPPERS V1"
NEXT_MARKER = "# ✅ ROM 9.0.2 PLAYER SYSTEM FACADE WRAPPERS V1"


def make_backup(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    target = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def build_character_system():
    return r'''# ROM 9.0.12b character system real implementation
from __future__ import annotations

from datetime import datetime
import re

from data.classes import CLASS_CONFIGS, CLASS_RESET_SPHERE_ITEM_ID

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 24
NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ0-9 _'-]+$")


def _db():
    import db
    return db


def init_character_class_system():
    db = _db()
    migrations = [
        ("character_name", "TEXT DEFAULT ''"),
        ("character_class", "TEXT DEFAULT ''"),
        ("class_selected_at", "TEXT DEFAULT ''"),
        ("class_change_available", "INTEGER DEFAULT 0"),
        ("mp", "INTEGER DEFAULT 0"),
        ("max_mp", "INTEGER DEFAULT 0"),
        ("last_regen_at", "TEXT DEFAULT ''"),
    ]
    for column, column_type in migrations:
        try:
            db.cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {column_type}")
        except Exception:
            pass
    db.conn.commit()
    return True


def normalize_character_name(name):
    return re.sub(r"\s+", " ", str(name or "").strip())


def validate_character_name(name):
    value = normalize_character_name(name)
    if len(value) < NAME_MIN_LENGTH:
        return False, f"Ім’я має містити щонайменше {NAME_MIN_LENGTH} символи."
    if len(value) > NAME_MAX_LENGTH:
        return False, f"Ім’я має містити не більше {NAME_MAX_LENGTH} символів."
    if not NAME_PATTERN.fullmatch(value):
        return False, "Ім’я містить недозволені символи."
    return True, ""


def is_character_name_taken(name, exclude_user_id=None):
    init_character_class_system()
    db = _db()
    normalized = normalize_character_name(name).casefold()
    db.cursor.execute("SELECT user_id, character_name FROM users WHERE TRIM(COALESCE(character_name, '')) <> ''")
    for user_id, existing in db.cursor.fetchall():
        if exclude_user_id is not None and int(user_id) == int(exclude_user_id):
            continue
        if normalize_character_name(existing).casefold() == normalized:
            return True
    return False


def get_character_name(user_id):
    init_character_class_system()
    db = _db()
    db.cursor.execute("SELECT character_name FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    return normalize_character_name(row[0] if row else "")


def set_character_name(user_id, name):
    init_character_class_system()
    db = _db()
    value = normalize_character_name(name)
    valid, message = validate_character_name(value)
    if not valid:
        return {"success": False, "message": f"❌ {message}"}
    if is_character_name_taken(value, exclude_user_id=user_id):
        return {"success": False, "message": "❌ Це ім’я вже зайняте іншим персонажем."}
    db.cursor.execute("UPDATE users SET character_name=? WHERE user_id=?", (value, user_id))
    db.conn.commit()
    return {"success": True, "message": "✅ Ім’я персонажа збережено.", "character_name": value}


def get_character_class(user_id):
    init_character_class_system()
    db = _db()
    db.cursor.execute("SELECT character_class FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    return str((row[0] if row else "") or "").strip().lower()


def get_character_class_display(user_id):
    key = get_character_class(user_id)
    return CLASS_CONFIGS.get(key, {}).get("name", "Не обрано")


def get_character_resource_type(user_id):
    key = get_character_class(user_id)
    return CLASS_CONFIGS.get(key, {}).get("resource", "")


def get_max_mp(user_id):
    if get_character_resource_type(user_id) != "mana":
        return 0
    db = _db()
    db.cursor.execute("SELECT level, intelligence, wis FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    if not row:
        return 0
    level, intelligence, wisdom = (int(value or 0) for value in row)
    return max(0, 100 + level * 20 + intelligence * 3 + wisdom * 2)


def refresh_user_mp(user_id):
    init_character_class_system()
    db = _db()
    maximum = get_max_mp(user_id)
    db.cursor.execute("SELECT mp, max_mp FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    if not row:
        return 0
    current = int(row[0] or 0)
    old_max = int(row[1] or 0)
    if maximum <= 0:
        current = 0
    elif old_max <= 0 and current <= 0:
        current = maximum
    else:
        current = min(current, maximum)
    db.cursor.execute("UPDATE users SET mp=?, max_mp=? WHERE user_id=?", (current, maximum, user_id))
    db.conn.commit()
    return current


def get_user_mp(user_id):
    refresh_user_mp(user_id)
    db = _db()
    db.cursor.execute("SELECT mp FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    return int((row[0] if row else 0) or 0)


def set_user_mp(user_id, amount):
    init_character_class_system()
    db = _db()
    maximum = get_max_mp(user_id)
    try:
        value = int(amount)
    except Exception:
        value = 0
    value = max(0, min(value, maximum))
    db.cursor.execute("UPDATE users SET mp=?, max_mp=? WHERE user_id=?", (value, maximum, user_id))
    db.conn.commit()
    return value


def set_character_class(user_id, class_key):
    init_character_class_system()
    db = _db()
    key = str(class_key or "").strip().lower()
    if key not in CLASS_CONFIGS:
        return {"success": False, "message": "❌ Невідомий клас персонажа."}
    db.cursor.execute(
        "UPDATE users SET character_class=?, class_selected_at=? WHERE user_id=?",
        (key, datetime.now().isoformat(), user_id),
    )
    db.conn.commit()
    refresh_user_mp(user_id)
    return {"success": True, "message": f"✅ Обрано клас: {CLASS_CONFIGS[key]['name']}", "class_key": key}


def get_class_change_available(user_id):
    init_character_class_system()
    db = _db()
    db.cursor.execute("SELECT class_change_available FROM users WHERE user_id=?", (user_id,))
    row = db.cursor.fetchone()
    return max(0, int((row[0] if row else 0) or 0))


def has_class_change_available(user_id):
    return get_class_change_available(user_id) > 0


def grant_class_change_available(user_id, amount=1):
    init_character_class_system()
    db = _db()
    try:
        amount = max(1, int(amount))
    except Exception:
        amount = 1
    db.cursor.execute(
        "UPDATE users SET class_change_available=COALESCE(class_change_available, 0)+? WHERE user_id=?",
        (amount, user_id),
    )
    db.conn.commit()
    return get_class_change_available(user_id)


def consume_class_change_available(user_id):
    init_character_class_system()
    db = _db()
    db.cursor.execute(
        "UPDATE users SET class_change_available=class_change_available-1 WHERE user_id=? AND COALESCE(class_change_available, 0)>0",
        (user_id,),
    )
    changed = db.cursor.rowcount > 0
    db.conn.commit()
    return changed


def needs_character_name(user_id):
    return get_character_name(user_id) == ""


def needs_character_class(user_id):
    return get_character_class(user_id) == ""


def get_class_reset_sphere_item_id():
    return int(CLASS_RESET_SPHERE_ITEM_ID)
'''


def build_db_facade():
    return r'''# ==============================
# ROM 9.0.12b CHARACTER SYSTEM REAL IMPLEMENTATION V1
# ==============================

def _character_system_v2():
    from systems import character_system as _mod
    return _mod


def normalize_character_name(name):
    return _character_system_v2().normalize_character_name(name)


def validate_character_name(name):
    return _character_system_v2().validate_character_name(name)


def get_character_name(user_id):
    return _character_system_v2().get_character_name(user_id)


def set_character_name(user_id, name):
    return _character_system_v2().set_character_name(user_id, name)


def get_character_class(user_id):
    return _character_system_v2().get_character_class(user_id)


def set_character_class(user_id, class_key):
    return _character_system_v2().set_character_class(user_id, class_key)


def get_character_class_display(user_id):
    return _character_system_v2().get_character_class_display(user_id)


def get_character_resource_type(user_id):
    return _character_system_v2().get_character_resource_type(user_id)


def get_user_mp(user_id):
    return _character_system_v2().get_user_mp(user_id)


def set_user_mp(user_id, mp):
    return _character_system_v2().set_user_mp(user_id, mp)


def get_max_mp(user_id):
    return _character_system_v2().get_max_mp(user_id)


def refresh_user_mp(user_id):
    return _character_system_v2().refresh_user_mp(user_id)


def grant_class_change_available(user_id, amount=1):
    return _character_system_v2().grant_class_change_available(user_id, amount)


def consume_class_change_available(user_id):
    return _character_system_v2().consume_class_change_available(user_id)


def get_class_change_available(user_id):
    return _character_system_v2().get_class_change_available(user_id)


def has_class_change_available(user_id):
    return _character_system_v2().has_class_change_available(user_id)


try:
    from data.classes import CLASS_CONFIGS, CLASS_RESET_SPHERE_ITEM_ID
except Exception:
    pass
'''


def replace_old_facade(text):
    start = text.find(OLD_MARKER)
    end = text.find(NEXT_MARKER)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("Не знайдено межі character facade 9.0.1 у db.py")
    start = text.rfind("# ==============================", 0, start)
    end = text.rfind("# ==============================", 0, end)
    return text[:start] + build_db_facade().rstrip() + "\n\n" + text[end:]


def main():
    root = Path(__file__).resolve().parents[1]
    db_path = root / "db.py"
    char_path = root / "systems" / "character_system.py"
    classes_path = root / "data" / "classes.py"

    for path in (db_path, char_path, classes_path):
        if not path.exists():
            raise SystemExit(f"❌ Не знайдено файл: {path}")

    if MARKER in db_path.read_text(encoding="utf-8"):
        print("ℹ️ Патч 9.0.12b уже застосовано.")
        return

    old_db = db_path.read_text(encoding="utf-8")
    old_char = char_path.read_text(encoding="utf-8")
    backups = [make_backup(root, db_path), make_backup(root, char_path)]

    try:
        char_path.write_text(build_character_system(), encoding="utf-8")
        db_path.write_text(replace_old_facade(old_db), encoding="utf-8")
        py_compile.compile(str(char_path), doraise=True)
        py_compile.compile(str(db_path), doraise=True)
        result = subprocess.run(
            [sys.executable, "-c", "import db; import systems.character_system as c; print(c.get_class_reset_sphere_item_id())"],
            cwd=str(root), capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
    except Exception as error:
        db_path.write_text(old_db, encoding="utf-8")
        char_path.write_text(old_char, encoding="utf-8")
        raise SystemExit(f"❌ Патч не застосовано; файли відновлено.\n{error}")

    print("✅ Патч 9.0.12b Character System Real Implementation застосовано успішно.")
    print("✅ character/class/MP API більше не делегується у character _legacy_* refs.")
    print("Backup:")
    for item in backups:
        print(f"- {item}")
    print("\nПеревірки:")
    print("python -m py_compile .\\systems\\character_system.py")
    print("python -m py_compile .\\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
