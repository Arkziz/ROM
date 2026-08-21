# ROM 17.12.1.2 FORBIDDEN NON-UKRAINIAN CYRILLIC NAME LETTERS
# ROM 17.12.1 CHARACTER NAME VALIDATION
# ROM 9.0.12b character system real implementation
from __future__ import annotations

from datetime import datetime
import re
import unicodedata

from data.classes import CLASS_CONFIGS, CLASS_RESET_SPHERE_ITEM_ID

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 24
NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ0-9 _'-]+$")
FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS = frozenset("ёЁъЪыЫэЭ")


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
    value = str(name or "").strip()
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value)


def validate_character_name(name):
    value = normalize_character_name(name)
    if len(value) < NAME_MIN_LENGTH:
        return False, f"Ім’я має містити щонайменше {NAME_MIN_LENGTH} символи."
    if len(value) > NAME_MAX_LENGTH:
        return False, f"Ім’я має містити не більше {NAME_MAX_LENGTH} символів."
    if any(char in FORBIDDEN_NON_UKRAINIAN_CYRILLIC_LETTERS for char in value):
        return False, "Ім'я не повинно містити літери мови ворога."
    if not any(char.isalpha() for char in value):
        return False, "Ім’я має містити хоча б одну літеру."
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


# ==============================
# ✅ HOTFIX 9.0.12b1: CHARACTER MP RETURN CONTRACT FIX
# ==============================

def get_user_mp(user_id):
    """
    Повертає MP у старому публічному форматі ROM.

    Важливо:
    handlers/profile.py та handlers/combat.py очікують словник:

        {
            "mp": current_mp,
            "max_mp": max_mp
        }

    Після refactor 9.0.12b функція помилково повертала int,
    через що виникало:

        AttributeError: 'int' object has no attribute 'get'
    """

    import db as _db

    try:
        user_id = int(user_id)
    except Exception:
        user_id = 0

    max_mp = int(get_max_mp(user_id) or 0)

    row = _db.conn.execute(
        """
        SELECT mp
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()

    if not row:
        current_mp = max_mp
    else:
        try:
            current_mp = int(row[0] or 0)
        except Exception:
            current_mp = max_mp

    current_mp = max(0, min(current_mp, max_mp))

    return {
        "mp": current_mp,
        "max_mp": max_mp,
        "current_mp": current_mp
    }

# ==============================
# ROM 10.7.0 RUNE-AWARE MAX MP
# ==============================

_RUNE_STATS_BASE_GET_MAX_MP_10_7_0 = get_max_mp


def get_max_mp(user_id):
    """Mana formula with equipped, unbroken INT/WIS rune bonuses."""
    if get_character_resource_type(user_id) != "mana":
        return 0
    db = _db()
    row = db.conn.execute(
        "SELECT level, intelligence, wis FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return 0
    level, intelligence, wisdom = (int(value or 0) for value in row)
    try:
        from systems.rune_system import get_equipped_rune_stat_totals
        rune = get_equipped_rune_stat_totals(user_id)
    except Exception:
        rune = {}
    intelligence += int(rune.get("int", 0) or 0)
    wisdom += int(rune.get("wis", 0) or 0)
    return max(0, 100 + level * 20 + intelligence * 3 + wisdom * 2)

