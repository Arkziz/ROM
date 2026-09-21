# ROM 17.18.2.2 BOW CROSSBOW DAMAGE DIFFERENTIATION
# ROM 17.13.1.1 DEFAULT BAG SLOTS IMPORT RECOVERY
"""
Player management module - wrapper for systems.player_system
"""

from data.player_progression import get_exp_to_next_level

from .connection import conn, cursor, DEFAULT_BAG_SLOTS
from data.player_hp import get_starting_max_hp


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


def get_enemy_crit_chance_against_player(user_id):
    """
    Шанс криту ворога по гравцю.
    Формула: max(0, 10 - STA // 25)
    """
    stats = get_player_stats(user_id)

    if not stats:
        return 10.0

    total_str, total_dex, total_int, total_wis, total_sta, level = stats
    chance = max(0, 10 - (total_sta // 25))
    
    return chance


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
    from datetime import datetime, timezone
    
    # Import systems that need initialization
    from systems.energy_system import init_energy_system
    
    init_energy_system()
    starting_max_hp = get_starting_max_hp()
    registered_at = datetime.now(timezone.utc).isoformat()
    
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
        energy_full_notified,
        registered_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        starting_max_hp,
        starting_max_hp,
        1,
        0,
        0.0,
        0,
        DEFAULT_BAG_SLOTS,  # ROM 17.8.1 BASE BAG CAPACITY 60
        "start_path",  # ROM 18.23.3 new characters start at Початок Шляху
        10,
        10,
        10,
        10,
        10,
        None,
        None,
        0,
        datetime.now().isoformat(),
        1,
        registered_at
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


# ==============================
# COMBAT PROFILE
# ==============================

def get_player_attack_profile(user_id):
    """Return weapon profile with stat attack from canonical production APIs."""
    from .equipment import get_equipped_slot, get_weapon_damage_by_inventory_id

    stats = get_player_stats(user_id)
    if not stats:
        return {
            "weapon_subtype": "",
            "attack_type": "physical",
            "stat_attack": 0,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": 0,
            "weapon_text": "Без зброї",
        }

    physical_stat_attack = get_attack(user_id)
    magical_stat_attack = get_magic_attack(user_id)
    main_hand_id = get_equipped_slot(user_id, "main_hand")

    if not main_hand_id:
        return {
            "weapon_subtype": "",
            "attack_type": "physical",
            "stat_attack": physical_stat_attack,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": physical_stat_attack,
            "weapon_text": "Без зброї",
        }

    weapon_data = get_weapon_damage_by_inventory_id(main_hand_id)
    if not weapon_data.get("is_weapon"):
        return {
            "weapon_subtype": "",
            "attack_type": "physical",
            "stat_attack": physical_stat_attack,
            "weapon_min_damage": 0,
            "weapon_max_damage": 0,
            "display_attack": physical_stat_attack,
            "weapon_text": "Без зброї",
        }

    attack_type = weapon_data["attack_type"]
    if attack_type == "magical":
        stat_attack = magical_stat_attack
        weapon_min = weapon_data["magic_min"]
        weapon_max = weapon_data["magic_max"]
    else:
        stat_attack = physical_stat_attack
        weapon_min = weapon_data["physical_min"]
        weapon_max = weapon_data["physical_max"]

    display_attack = stat_attack + weapon_max
    return {
        "weapon_subtype": str(weapon_data.get("item_subtype") or "").strip().lower(),
        "attack_type": attack_type,
        "stat_attack": stat_attack,
        "weapon_min_damage": weapon_min,
        "weapon_max_damage": weapon_max,
        "display_attack": display_attack,
        "weapon_text": weapon_data.get("text"),
    }


