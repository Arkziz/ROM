# ROM 17.15.1 PERSISTENT MANA REGENERATION
# ROM 17.13.1 CLASS SELECTION PREVIEW CONFIRMATION
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
    """Return persisted current MP after canonical lazy regeneration."""
    try:
        user_id = int(user_id)
    except Exception:
        user_id = 0
    data = apply_lazy_mp_regeneration_17_15_1(user_id)
    current_mp = int(data.get("mp", 0) or 0)
    max_mp = int(data.get("max_mp", 0) or 0)
    return {"mp": current_mp, "max_mp": max_mp, "current_mp": current_mp}

# ==============================
# ROM 10.7.0 RUNE-AWARE MAX MP
# ==============================

_RUNE_STATS_BASE_GET_MAX_MP_10_7_0 = get_max_mp


def get_max_mp(user_id):
    """Canonical Max MP from exact-once effective INT/WIS totals."""
    if get_character_resource_type(user_id) != "mana":
        return 0
    db = _db()
    row = db.conn.execute(
        "SELECT level FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return 0
    from systems.player_system import get_player_stats
    from systems.stat_system import calculate_max_mp
    stats = get_player_stats(user_id)
    if not stats or len(stats) < 5:
        return 0
    _strength, _dexterity, intelligence, wisdom, _stamina = stats[:5]
    return calculate_max_mp(
        get_character_class(user_id),
        level=int(row[0] or 0),
        intelligence=intelligence,
        wisdom=wisdom,
    )

# Stage 17.13.1 atomic confirmation services.
def confirm_initial_character_class_17_13_1(user_id, class_key):
    init_character_class_system()
    db = _db()
    key = str(class_key or "").strip().lower()
    if key not in CLASS_CONFIGS:
        return {"success": False, "message": "❌ Невідомий клас персонажа."}
    try:
        db.conn.execute("BEGIN IMMEDIATE")
        row = db.cursor.execute(
            "SELECT TRIM(COALESCE(character_name,'')), TRIM(COALESCE(character_class,'')) FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row or not row[0]:
            db.conn.rollback()
            return {"success": False, "message": "❌ Спочатку потрібно вказати ім’я персонажа."}
        if row[1]:
            db.conn.rollback()
            return {"success": False, "message": "ℹ️ Клас персонажа вже обрано."}
        db.cursor.execute(
            "UPDATE users SET character_class=?, class_selected_at=? WHERE user_id=? AND TRIM(COALESCE(character_class,''))=''",
            (key, datetime.now().isoformat(), user_id),
        )
        if db.cursor.rowcount != 1:
            db.conn.rollback()
            return {"success": False, "message": "ℹ️ Клас персонажа вже обрано."}
        db.conn.commit()
    except Exception as error:
        try:
            db.conn.rollback()
        except Exception:
            pass
        return {"success": False, "message": f"❌ Не вдалося підтвердити клас: {error}"}
    refresh_user_mp(user_id)
    return {"success": True, "message": f"✅ Обрано клас: {CLASS_CONFIGS[key]['name']}", "class_key": key}


def confirm_character_class_change_17_13_1(user_id, class_key):
    init_character_class_system()
    db = _db()
    key = str(class_key or "").strip().lower()
    if key not in CLASS_CONFIGS:
        return {"success":False,"message":"❌ Невідомий клас персонажа."}
    row = db.cursor.execute("""SELECT TRIM(COALESCE(character_class,'')),
        COALESCE(class_change_available,0),pending_class_change_inventory_id
        FROM users WHERE user_id=?""",(int(user_id),)).fetchone()
    if not row:return {"success":False,"message":"❌ Персонажа не знайдено."}
    if str(row[0] or "")==key:return {"success":False,"message":"ℹ️ Цей клас уже обрано."}
    if int(row[1] or 0)<=0 or row[2] is None:return {"success":False,"message":"❌ Зміна класу недоступна."}
    from systems.attribute_respec_system import reset_allocated_attributes,AttributeRespecError
    from systems.player_system import get_max_hp,get_max_mp
    try:
        result=reset_allocated_attributes(int(user_id),int(row[2]),
            f"class_change:{int(user_id)}:{int(row[2])}:{key}",operation_type="class_change",
            new_class=key,expected_item_id=CLASS_RESET_SPHERE_ITEM_ID,db_module=db,
            max_hp_getter=get_max_hp,max_mp_getter=get_max_mp)
        db.cursor.execute("""UPDATE users SET class_selected_at=?,class_change_available=0,
            pending_class_change_inventory_id=NULL WHERE user_id=?""",(datetime.now().isoformat(),int(user_id)))
        db.conn.commit()
    except AttributeRespecError as error:
        return {"success":False,"message":f"❌ Не вдалося підтвердити зміну класу: {error}"}
    return {"success":True,"message":f"✅ Обрано клас: {CLASS_CONFIGS[key]['name']}",
        "class_key":key,"old_class_key":str(row[0] or ""),
        "returned_points":int(result["before"]["returned_points"])}


# Stage 17.15.1 persistent MP helpers.
MP_REGEN_PERCENT_PER_MINUTE_17_15_1 = 0.30
MP_POST_COMBAT_FLOOR_PERCENT_17_15_1 = 0.30


def init_persistent_mp_columns_17_15_1():
    db = _db()
    columns = {str(row[1]) for row in db.cursor.execute("PRAGMA table_info(users)").fetchall()}
    additions = {
        "last_mp_regen_update": "TEXT DEFAULT ''",
        "mp_full_notified": "INTEGER DEFAULT 1",
        "mp_regen_paused": "INTEGER DEFAULT 0",
    }
    for name, declaration in additions.items():
        if name not in columns:
            db.cursor.execute(f"ALTER TABLE users ADD COLUMN {name} {declaration}")
    db.conn.commit()


def reset_mp_regen_clock_17_15_1(user_id, paused=None):
    init_persistent_mp_columns_17_15_1()
    db = _db()
    now = datetime.now().isoformat()
    if paused is None:
        db.cursor.execute(
            "UPDATE users SET last_mp_regen_update=? WHERE user_id=?",
            (now, int(user_id)),
        )
    else:
        db.cursor.execute(
            "UPDATE users SET last_mp_regen_update=?, mp_regen_paused=? WHERE user_id=?",
            (now, 1 if paused else 0, int(user_id)),
        )
    db.conn.commit()


def begin_mp_combat_pause_17_15_1(user_id):
    result = apply_lazy_mp_regeneration_17_15_1(user_id)
    reset_mp_regen_clock_17_15_1(user_id, paused=True)
    return result


def apply_lazy_mp_regeneration_17_15_1(user_id, now=None):
    """Regenerate MP without banking ticks across a Max MP boundary change."""
    init_persistent_mp_columns_17_15_1()
    db = _db()
    maximum = int(get_max_mp(user_id) or 0)
    current_time = now or datetime.now()
    row = db.cursor.execute(
        "SELECT mp, max_mp, last_mp_regen_update, COALESCE(mp_regen_paused,0) FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return {"success": False, "restored": 0, "mp": 0, "max_mp": maximum, "ticks": 0}
    stored_current = max(0, int(row[0] or 0))
    stored_maximum = max(0, int(row[1] or 0))
    paused = bool(int(row[3] or 0))
    if maximum <= 0:
        db.cursor.execute(
            "UPDATE users SET mp=0, max_mp=0, last_mp_regen_update=?, mp_full_notified=1 WHERE user_id=?",
            (current_time.isoformat(), int(user_id)),
        )
        db.conn.commit()
        return {"success": True, "restored": 0, "mp": 0, "max_mp": 0, "ticks": 0}
    current = min(stored_current, maximum)
    if maximum != stored_maximum:
        db.cursor.execute(
            "UPDATE users SET mp=?, max_mp=?, last_mp_regen_update=?, mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE 1 END WHERE user_id=?",
            (current, maximum, current_time.isoformat(), current, maximum, int(user_id)),
        )
        db.conn.commit()
        return {"success": True, "restored": 0, "mp": current, "max_mp": maximum, "ticks": 0, "maximum_changed": True}
    try:
        last = datetime.fromisoformat(str(row[2] or ""))
    except Exception:
        last = current_time
        db.cursor.execute(
            "UPDATE users SET mp=?, max_mp=?, last_mp_regen_update=? WHERE user_id=?",
            (current, maximum, last.isoformat(), int(user_id)),
        )
        db.conn.commit()
        return {"success": True, "restored": 0, "mp": current, "max_mp": maximum, "ticks": 0}
    if paused or current >= maximum:
        db.cursor.execute(
            "UPDATE users SET mp=?, max_mp=?, last_mp_regen_update=?, mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE mp_full_notified END WHERE user_id=?",
            (current, maximum, current_time.isoformat(), current, maximum, int(user_id)),
        )
        db.conn.commit()
        return {"success": True, "restored": 0, "mp": current, "max_mp": maximum, "ticks": 0}
    ticks = max(0, int((current_time - last).total_seconds() // 60))
    if ticks <= 0:
        return {"success": True, "restored": 0, "mp": current, "max_mp": maximum, "ticks": 0}
    per_tick = max(1, int(maximum * MP_REGEN_PERCENT_PER_MINUTE_17_15_1))
    new_mp = min(maximum, current + per_tick * ticks)
    new_stamp = datetime.fromtimestamp(last.timestamp() + ticks * 60).isoformat()
    db.cursor.execute(
        "UPDATE users SET mp=?, max_mp=?, last_mp_regen_update=?, mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE mp_full_notified END WHERE user_id=?",
        (new_mp, maximum, new_stamp, new_mp, maximum, int(user_id)),
    )
    db.conn.commit()
    return {"success": True, "restored": new_mp-current, "mp": new_mp, "max_mp": maximum, "ticks": ticks}


def apply_post_combat_mp_floor_17_15_1(user_id):
    init_persistent_mp_columns_17_15_1()
    db = _db()
    maximum = int(get_max_mp(user_id) or 0)
    if maximum <= 0:
        reset_mp_regen_clock_17_15_1(user_id, paused=False)
        return {"success": True, "restored": False, "mp": 0, "max_mp": 0}
    row = db.cursor.execute("SELECT mp FROM users WHERE user_id=?", (int(user_id),)).fetchone()
    current = max(0, min(int((row[0] if row else 0) or 0), maximum))
    floor_value = max(1, int(maximum * MP_POST_COMBAT_FLOOR_PERCENT_17_15_1))
    new_mp = max(current, floor_value)
    db.cursor.execute(
        "UPDATE users SET mp=?, max_mp=?, last_mp_regen_update=?, mp_regen_paused=0, mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE mp_full_notified END WHERE user_id=?",
        (new_mp, maximum, datetime.now().isoformat(), new_mp, maximum, int(user_id)),
    )
    db.conn.commit()
    return {"success": True, "restored": new_mp>current, "mp": new_mp, "max_mp": maximum}

