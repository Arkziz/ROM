"""
Character management module - wrapper for systems.character_system
"""


def _character_system():
    from systems import character_system
    return character_system


# ==============================
# CHARACTER NAME
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
