"""
Character management module - wrapper for systems.character_system
"""


def _character_system():
    from systems import character_system
    return character_system


# ==============================
# IMPORTS FROM DATA
# ==============================

from data.classes import CLASS_CONFIGS


# ==============================
# INITIALIZATION
# ==============================

def init_character_class_system():
    """Ініціалізує систему класів персонажів."""
    return _character_system().init_character_class_system()


# ==============================# CHARACTER NAME
# ==============================

def normalize_character_name(name):
    return _character_system().normalize_character_name(name)


def validate_character_name(name):
    return _character_system().validate_character_name(name)


def get_character_name(user_id):
    return _character_system().get_character_name(user_id)


def set_character_name(user_id, name):
    return _character_system().set_character_name(user_id, name)


def is_character_name_taken(name, exclude_user_id=None):
    """
    Перевіряє чи зайняте ім'я персонажа іншим користувачем.
    """
    from .connection import cursor
    
    from systems.character_system import normalize_character_name
    
    target_name = normalize_character_name(name)
    
    if not target_name:
        return False
    
    cursor.execute("""
    SELECT user_id, character_name
    FROM users
    WHERE character_name IS NOT NULL
      AND character_name != ''
    """)
    
    rows = cursor.fetchall()
    
    for row in rows:
        existing_user_id, existing_name = row
        
        if exclude_user_id is not None:
            try:
                if int(existing_user_id) == int(exclude_user_id):
                    continue
            except Exception:
                pass
        
        existing_normalized = normalize_character_name(existing_name)
        
        if existing_normalized.casefold() == target_name.casefold():
            return True
    
    return False


def needs_character_name(user_id):
    """Перевіряє чи потрібно встановити ім'я персонажа."""
    return _character_system().needs_character_name(user_id)


def needs_character_class(user_id):
    """Перевіряє чи потрібно обрати клас персонажа."""
    return _character_system().needs_character_class(user_id)


# ==============================
# CHARACTER CLASS
# ==============================

def get_character_class(user_id):
    return _character_system().get_character_class(user_id)


def set_character_class(user_id, class_key):
    return _character_system().set_character_class(user_id, class_key)


def get_character_class_display(user_id):
    return _character_system().get_character_class_display(user_id)


def get_character_resource_type(user_id):
    return _character_system().get_character_resource_type(user_id)


# ==============================
# MP MANAGEMENT
# ==============================

def get_user_mp(user_id):
    return _character_system().get_user_mp(user_id)


def set_user_mp(user_id, mp):
    return _character_system().set_user_mp(user_id, mp)


def spend_user_mp(user_id, amount):
    """
    Витрата MP для навичок.
    """
    from .connection import conn, cursor
    
    mp_data = get_user_mp(user_id)

    current_mp = mp_data.get("mp", 0)
    max_mp = mp_data.get("max_mp", 0)

    try:
        amount = int(amount)
    except Exception:
        amount = 0

    if amount <= 0:
        return {
            "success": True,
            "mp": current_mp,
            "max_mp": max_mp
        }

    if current_mp < amount:
        return {
            "success": False,
            "message": (
                f"❌ Недостатньо мани.\n\n"
                f"🔵 Потрібно: {amount} MP\n"
                f"🔵 У тебе: {current_mp}/{max_mp} MP"
            ),
            "mp": current_mp,
            "max_mp": max_mp
        }

    new_mp = current_mp - amount

    cursor.execute("""
    UPDATE users
    SET mp=?
    WHERE user_id=?
    """, (
        new_mp,
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "mp": new_mp,
        "max_mp": max_mp
    }


def restore_user_mp_to_full(user_id):
    """
    Повністю відновлює MP, якщо персонаж використовує ману.

    Для не-mana класів нічого не робить.
    """
    from .connection import conn, cursor
    from data.classes import CLASS_CONFIGS
    
    init_character_class_system()

    class_key = get_character_class(user_id)
    resource_type = CLASS_CONFIGS.get(class_key, {}).get("resource", "")

    if resource_type != "mana":
        return {
            "success": True,
            "restored": False,
            "mp": 0,
            "max_mp": 0
        }

    mp_data = get_user_mp(user_id)
    max_mp = mp_data.get("max_mp", 0)

    cursor.execute("""
    UPDATE users
    SET mp=?
    WHERE user_id=?
    """, (
        max_mp,
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "restored": True,
        "mp": max_mp,
        "max_mp": max_mp
    }


def get_max_mp(user_id):
    return _character_system().get_max_mp(user_id)


def refresh_user_mp(user_id):
    return _character_system().refresh_user_mp(user_id)


# ==============================
# CLASS CHANGE TOKENS
# ==============================

def grant_class_change_available(user_id, amount=1):
    return _character_system().grant_class_change_available(user_id, amount)


def consume_class_change_available(user_id):
    return _character_system().consume_class_change_available(user_id)


def get_class_change_available(user_id):
    return _character_system().get_class_change_available(user_id)


def has_class_change_available(user_id):
    return _character_system().has_class_change_available(user_id)


# ==============================
# CHARACTER PROFILE
# ==============================

def get_character_profile_summary(user_id):
    """
    Повертає зведену інформацію про персонажа для профілю.
    """
    init_character_class_system()

    return {
        "name": get_character_name(user_id),
        "class_key": get_character_class(user_id),
        "class_name": get_character_class_display(user_id),
        "resource_type": get_character_resource_type(user_id),
        "mp_data": get_user_mp(user_id)
    }
