"""
Player management module - wrapper for systems.player_system
"""

from .connection import conn, cursor


# ==============================
# PLAYER PROGRESSION
# ==============================

def _player_system():
    from systems import player_system
    return player_system


def get_player_level(user_id):
    return _player_system().get_player_level(user_id)


def get_player_stats(user_id):
    return _player_system().get_player_stats(user_id)


def get_user_progress(user_id):
    return _player_system().get_user_progress(user_id)


def add_exp(user_id, amount):
    return _player_system().add_exp(user_id, amount)


# ==============================
# WALLET AND ECONOMY
# ==============================

def get_wallet(user_id):
    return _player_system().get_wallet(user_id)


def add_gold(user_id, amount):
    return _player_system().add_gold(user_id, amount)


def add_kill(user_id, amount=1):
    return _player_system().add_kill(user_id, amount)


# ==============================
# COMBAT STATS
# ==============================

def get_attack(user_id):
    return _player_system().get_attack(user_id)


def get_magic_attack(user_id):
    return _player_system().get_magic_attack(user_id)


def get_physical_defense(user_id):
    return _player_system().get_physical_defense(user_id)


def get_magic_defense(user_id):
    return _player_system().get_magic_defense(user_id)


def get_physical_crit_chance_display(user_id):
    return _player_system().get_physical_crit_chance_display(user_id)


def get_magical_crit_chance_display(user_id):
    return _player_system().get_magical_crit_chance_display(user_id)


def get_base_dodge_chance_display(user_id):
    return _player_system().get_base_dodge_chance_display(user_id)


# ==============================
# HP MANAGEMENT
# ==============================

def get_max_hp(user_id):
    return _player_system().get_max_hp(user_id)


def get_current_hp_raw(user_id):
    return _player_system().get_current_hp_raw(user_id)


def get_current_hp(user_id):
    return _player_system().get_current_hp(user_id)


def set_current_hp(user_id, hp):
    return _player_system().set_current_hp(user_id, hp)


def sync_user_max_hp(user_id, heal_to_full=False):
    return _player_system().sync_user_max_hp(user_id, heal_to_full=heal_to_full)


# ==============================
# USER CREATION
# ==============================

def create_user(user_id):
    """
    Створює нового користувача з початковими параметрами.
    """
    from datetime import datetime
    
    # Import systems that need initialization
    from systems.energy_system import init_energy_system
    
    init_energy_system()
    
    cursor.execute("""
    INSERT OR IGNORE INTO users (
        user_id,
        hp,
        max_hp,
        level,
        exp,
        gold,
        kills,
        bag_slots,
        current_location,
        str,
        dex,
        intelligence,
        wis,
        sta,
        equipped_weapon,
        equipped_armor,
        energy,
        last_energy_update,
        energy_full_notified
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        170,
        170,
        1,
        0,
        0.0,
        0,
        40,  # DEFAULT_BAG_SLOTS
        "start_path",
        10,
        10,
        10,
        10,
        10,
        None,
        None,
        0,
        datetime.now().isoformat(),
        1
    ))
    
    conn.commit()
    
    # Fix energy if needed
    cursor.execute("""
    UPDATE users
    SET energy = 0,
        last_energy_update = ?,
        energy_full_notified = 1
    WHERE user_id = ?
      AND (energy IS NULL OR energy < 0 OR energy > 40)
    """, (
        datetime.now().isoformat(),
        user_id,
    ))
    
    conn.commit()
    
    # Ensure equipment slots
    from systems.equipment_system import ensure_equipment_slots
    ensure_equipment_slots(user_id)
    
    return True


def get_user(user_id):
    """
    Отримує повні дані користувача.
    """
    cursor.execute("""
    SELECT *
    FROM users
    WHERE user_id=?
    """, (user_id,))
    
    return cursor.fetchone()
