# ROM 17.14.1 LEVEL UP REWARDS
# ✅ ROM 9.0.2 PLAYER SYSTEM V1
"""
ROM Player System v1.

Goal of 9.0.2:
- create a dedicated player/progression/stat domain module;
- move public player/stats/gold/exp/API ownership behind systems.player_system;
- keep db.py as compatibility facade for existing handlers;
- preserve current behavior by delegating to legacy db.py implementations where available.

This stage is conservative and intentionally does not delete old db.py code.
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from data.player_hp import calculate_base_max_hp, get_starting_max_hp
from data.player_combat_chances import CRIT_BASE_CHANCE, DODGE_BASE_CHANCE, calculate_magical_crit_chance, calculate_physical_crit_chance
from data.defense_policy import calculate_total_defense


def _db_module():
    import db
    return db


def _legacy_function(name: str) -> Optional[Callable[..., Any]]:
    db = _db_module()
    return getattr(db, f"_legacy_{name}_before_player_system_v1", None)


def _fetchone(sql: str, params: tuple = ()):  # sqlite3.Row or tuple depending on project state
    db = _db_module()
    db.cursor.execute(sql, params)
    return db.cursor.fetchone()


def _execute_commit(sql: str, params: tuple = ()):
    db = _db_module()
    db.cursor.execute(sql, params)
    db.conn.commit()


def _row_get(row, key: str, index: int = 0, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        pass
    try:
        return row[index]
    except Exception:
        return default


def get_player_stats(user_id: int):
    """Return total STR/DEX/INT/WIS/STA and level exactly once.

    Total primary stats are base database values plus bonuses from active,
    unbroken equipped items and runes installed in active, unbroken equipment.
    """
    row = _player_base_row_9_0_12g(user_id)
    if not row:
        return None
    base_str, base_dex, base_int, base_wis, base_sta, level = row
    db = _player_combat_db_9_0_12g()
    bonuses = db.get_item_bonuses(int(user_id))
    try:
        item_str, item_dex, item_int, item_wis, item_sta = bonuses
    except Exception:
        item_str = item_dex = item_int = item_wis = item_sta = 0
    try:
        from systems.rune_system import get_equipped_rune_stat_totals
        rune = get_equipped_rune_stat_totals(user_id)
    except Exception:
        rune = {}
    return (
        int(base_str or 0) + int(item_str or 0) + int(rune.get("str", 0) or 0),
        int(base_dex or 0) + int(item_dex or 0) + int(rune.get("dex", 0) or 0),
        int(base_int or 0) + int(item_int or 0) + int(rune.get("int", 0) or 0),
        int(base_wis or 0) + int(item_wis or 0) + int(rune.get("wis", 0) or 0),
        int(base_sta or 0) + int(item_sta or 0) + int(rune.get("sta", 0) or 0),
        max(1, int(level or 1)),
    )


def get_player_level(user_id: int):
    legacy = _legacy_function("get_player_level")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT level FROM users WHERE user_id=?", (user_id,))
    return int(_row_get(row, "level", 0, 1) or 1)


def get_wallet(user_id: int):
    legacy = _legacy_function("get_wallet")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT gold FROM users WHERE user_id=?", (user_id,))
    return float(_row_get(row, "gold", 0, 0) or 0)


def add_gold(user_id: int, amount):
    legacy = _legacy_function("add_gold")
    if legacy:
        return legacy(user_id, amount)

    current = get_wallet(user_id)
    new_value = current + float(amount)
    _execute_commit("UPDATE users SET gold=? WHERE user_id=?", (new_value, user_id))
    return new_value


def add_kill(user_id: int, amount: int = 1):
    legacy = _legacy_function("add_kill")
    if legacy:
        return legacy(user_id, amount)

    try:
        _execute_commit(
            "UPDATE users SET kills=COALESCE(kills, 0)+? WHERE user_id=?",
            (int(amount), user_id),
        )
    except Exception:
        # Some older DB versions might use a different column name.
        return False
    return True


def get_user_progress(user_id: int):
    """Return the historical six-key player progression dictionary."""
    db = _db_module()
    row = _fetchone(
        """
        SELECT level, exp, gold, kills, daily_hunts
        FROM users
        WHERE user_id=?
        """,
        (user_id,),
    )
    if not row:
        return None

    level = int(_row_get(row, "level", 0, 1) or 1)
    return {
        "level": level,
        "exp": int(_row_get(row, "exp", 1, 0) or 0),
        "exp_to_next": db.get_exp_to_next_level(level),
        "gold": _row_get(row, "gold", 2, 0),
        "kills": _row_get(row, "kills", 3, 0),
        "daily_hunts": int(_row_get(row, "daily_hunts", 4, 0) or 0),
    }









def get_current_hp_raw(user_id: int):
    legacy = _legacy_function("get_current_hp_raw")
    if legacy:
        return legacy(user_id)

    row = _fetchone("SELECT hp FROM users WHERE user_id=?", (user_id,))
    return int(_row_get(row, "hp", 0, get_max_hp(user_id)) or get_max_hp(user_id))


def get_current_hp(user_id: int):
    legacy = _legacy_function("get_current_hp")
    if legacy:
        return legacy(user_id)
    return get_current_hp_raw(user_id)


def set_current_hp(user_id: int, hp: int):
    legacy = _legacy_function("set_current_hp")
    if legacy:
        return legacy(user_id, hp)

    max_hp = get_max_hp(user_id)
    safe_hp = max(0, min(int(hp), int(max_hp)))
    _execute_commit("UPDATE users SET hp=? WHERE user_id=?", (safe_hp, user_id))
    return safe_hp















# ==============================
# ✅ ROM 9.0.2a PLAYER ADD_KILL SIGNATURE FIX V1
# ==============================

try:
    _player_system_base_add_kill_before_signature_fix_v1 = add_kill
except NameError:
    _player_system_base_add_kill_before_signature_fix_v1 = None


def add_kill(user_id: int, amount: int = 1):
    """
    Compatibility fix.

    У старому db.py актуальна legacy-функція add_kill() має сигнатуру:
        add_kill(user_id)

    А facade 9.0.2 викликав legacy як:
        legacy(user_id, amount)

    Через це після бою виникало:
        TypeError: add_kill() takes 1 positional argument but 2 were given

    Правильна сумісна логіка:
    - якщо amount == 1, пробуємо старий legacy(user_id);
    - якщо amount > 1 і legacy підтримує тільки 1 аргумент, викликаємо legacy(user_id) кілька разів;
    - якщо legacy відсутній, використовуємо fallback UPDATE.
    """

    legacy = _legacy_function("add_kill")

    if legacy:
        try:
            return legacy(user_id, amount)
        except TypeError:
            safe_amount = max(1, int(amount or 1))
            result = None
            for _ in range(safe_amount):
                result = legacy(user_id)
            return result

    try:
        safe_amount = max(1, int(amount or 1))
        _execute_commit(
            "UPDATE users SET kills=COALESCE(kills, 0)+? WHERE user_id=?",
            (safe_amount, user_id),
        )
        return True
    except Exception:
        return False


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

# ==============================
# ✅ ROM 9.0.12c1 PLAYER PROGRESSION REAL IMPLEMENTATION V1
# ==============================
# Safe first slice. Complex EXP/progress/combat-stat contracts remain legacy.

def _player_direct_db():
    import db
    return db

def _player_direct_fetchone(sql, params=()):
    db = _player_direct_db()
    db.cursor.execute(sql, params)
    return db.cursor.fetchone()

def _player_direct_value(row, key, index=0, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        pass
    try:
        return row[index]
    except Exception:
        return default

def get_player_level(user_id: int):
    row = _player_direct_fetchone("SELECT level FROM users WHERE user_id=?", (int(user_id),))
    try:
        return int(_player_direct_value(row, "level", 0, 1) or 1)
    except Exception:
        return 1

def get_wallet(user_id: int):
    row = _player_direct_fetchone("SELECT gold FROM users WHERE user_id=?", (int(user_id),))
    try:
        return float(_player_direct_value(row, "gold", 0, 0.0) or 0.0)
    except Exception:
        return 0.0

def add_gold(user_id: int, amount):
    db = _player_direct_db()
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0
    db.cursor.execute("UPDATE users SET gold=COALESCE(gold,0)+? WHERE user_id=?", (amount, int(user_id)))
    db.conn.commit()
    return None

def add_kill(user_id: int, amount: int = 1):
    db = _player_direct_db()
    try:
        amount = max(0, int(amount))
    except Exception:
        amount = 1
    if amount:
        db.cursor.execute("UPDATE users SET kills=COALESCE(kills,0)+? WHERE user_id=?", (amount, int(user_id)))
        db.conn.commit()
    return None

def get_current_hp_raw(user_id: int):
    sync = sync_user_max_hp(int(user_id), heal_to_full=False)
    try:
        return int(sync.get("hp", 0) or 0)
    except Exception:
        return 0

def get_current_hp(user_id: int):
    return get_current_hp_raw(int(user_id))

def set_current_hp(user_id: int, hp: int):
    db = _player_direct_db()
    sync = sync_user_max_hp(int(user_id), heal_to_full=False)
    try:
        max_hp = int(sync.get("max_hp", get_max_hp(user_id)) or get_max_hp(user_id))
    except Exception:
        max_hp = int(get_max_hp(user_id) or 1)
    try:
        safe_hp = max(0, min(int(hp), max_hp))
    except Exception:
        safe_hp = 0
    db.cursor.execute("UPDATE users SET hp=? WHERE user_id=?", (safe_hp, int(user_id)))
    db.conn.commit()
    reset = getattr(db, "reset_hp_regen_timers_now", None)
    if callable(reset):
        reset(int(user_id))
    return safe_hp


# ==============================
# ROM 9.0.12g PLAYER COMBAT STATS REAL IMPLEMENTATION
# ==============================

_ARMOR_SLOTS_9_0_12G = {"helmet", "shoulders", "chest", "gloves", "legs", "boots"}


def _player_combat_db_9_0_12g():
    import db as _db_module
    return _db_module


def _player_base_row_9_0_12g(user_id):
    db = _player_combat_db_9_0_12g()
    return db.conn.execute(
        'SELECT COALESCE(str,0) + COALESCE(allocated_strength,0), COALESCE(dex,0) + COALESCE(allocated_dexterity,0), COALESCE(intelligence,0) + COALESCE(allocated_intelligence,0), COALESCE(wis,0) + COALESCE(allocated_wisdom,0), COALESCE(sta,0) + COALESCE(allocated_stamina,0), COALESCE(level,1) FROM users WHERE user_id=?',
        (int(user_id),),
    ).fetchone()




def get_attack(user_id):
    """Return production PATK through configurable Stat System scaling."""
    from systems.character_system import get_character_class
    from systems.stat_system import calculate_physical_attack

    strength, dexterity, intelligence, wisdom, stamina = get_player_stats(user_id)[:5]
    return calculate_physical_attack(
        get_character_class(user_id),
        strength=strength,
        dexterity=dexterity,
        intelligence=intelligence,
        wisdom=wisdom,
        stamina=stamina,
    )

def get_magic_attack(user_id):
    """Return production MATK through configurable Stat System scaling."""
    from systems.character_system import get_character_class
    from systems.stat_system import calculate_magical_attack

    strength, dexterity, intelligence, wisdom, stamina = get_player_stats(user_id)[:5]
    return calculate_magical_attack(
        get_character_class(user_id),
        strength=strength,
        dexterity=dexterity,
        intelligence=intelligence,
        wisdom=wisdom,
        stamina=stamina,
    )

def _armor_refine_hp_bonus_percent_9_0_12g(user_id):
    db = _player_combat_db_9_0_12g()
    rows = db.conn.execute(
        "SELECT it.slot_key, it.rarity, COALESCE(inv.refine_level,0), "
        "COALESCE(inv.durability,100) "
        "FROM equipment_slots es "
        "JOIN inventory inv ON inv.id=es.inventory_id AND inv.user_id=es.user_id "
        "JOIN items it ON it.id=inv.item_id "
        "WHERE es.user_id=?",
        (int(user_id),),
    ).fetchall()
    total = 0.0
    try:
        from systems.refine_system import get_armor_refine_hp_bonus_percent
    except Exception:
        return 0.0
    for slot_key, rarity, refine_level, durability in rows:
        if slot_key not in _ARMOR_SLOTS_9_0_12G:
            continue
        if int(durability or 0) <= 0:
            continue
        total += float(get_armor_refine_hp_bonus_percent(refine_level, rarity) or 0.0)
    return round(total, 4)


def get_max_hp(user_id: int):
    stats = get_player_stats(user_id)
    if not stats:
        return get_starting_max_hp()
    _str, _dex, _int, _wis, total_sta, level = stats
    base_hp = calculate_base_max_hp(level, total_sta)
    refine_percent = _armor_refine_hp_bonus_percent_9_0_12g(user_id)
    return max(1, int(round(base_hp * (1.0 + refine_percent / 100.0))))


def get_physical_defense(user_id):
    """Return Stage 18.14.2 PDEF through the accepted stat-system policy."""
    from systems.equipment_system import get_equipped_item_defenses
    from systems.stat_system import calculate_physical_defense

    _strength, _dexterity, _intelligence, _wisdom, stamina = get_player_stats(user_id)[:5]
    equipment_pdef, _equipment_mdef = get_equipped_item_defenses(user_id)
    return calculate_physical_defense(
        equipment_pdef=equipment_pdef,
        stamina=stamina,
    )



def get_magic_defense(user_id):
    """Return Stage 18.14.2 MDEF through the accepted stat-system policy."""
    from systems.equipment_system import get_equipped_item_defenses
    from systems.stat_system import calculate_magical_defense

    _strength, _dexterity, _intelligence, wisdom, _stamina = get_player_stats(user_id)[:5]
    _equipment_pdef, equipment_mdef = get_equipped_item_defenses(user_id)
    return calculate_magical_defense(
        equipment_mdef=equipment_mdef,
        wisdom=wisdom,
    )



def get_physical_crit_chance_display(user_id: int):
    stats=get_player_stats(user_id)
    return calculate_physical_crit_chance(stats[1]) if stats else CRIT_BASE_CHANCE


def get_magical_crit_chance_display(user_id: int):
    stats=get_player_stats(user_id)
    return calculate_magical_crit_chance(stats[3]) if stats else CRIT_BASE_CHANCE


def get_base_dodge_chance_display(user_id: int):
    return DODGE_BASE_CHANCE

# ==============================
# ROM 10.7.0 EQUIPPED RUNE STAT BONUSES
# ==============================




# Stage 17.14.1 authoritative transactional EXP override.
def add_exp(user_id: int, amount):
    """Apply EXP, stats, HP and exactly-once level rewards in one transaction."""
    db = _db_module()
    from systems.level_up_reward_system import (
        apply_level_up_rewards_in_transaction,
        build_level_up_reward_message,
        init_level_up_reward_system,
    )

    init_level_up_reward_system(db)
    db.conn.execute("BEGIN IMMEDIATE")
    try:
        row = db.cursor.execute(
            "SELECT level, exp FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row:
            db.conn.rollback()
            return None

        old_level = int(_row_get(row, "level", 0, 1) or 1)
        level = old_level
        exp = int(_row_get(row, "exp", 1, 0) or 0) + int(amount)
        reached_levels = []

        while exp >= db.get_exp_to_next_level(level):
            exp -= db.get_exp_to_next_level(level)
            level += 1
            reached_levels.append(level)

        level_ups = len(reached_levels)
        attribute_points_awarded = 0
        if level_ups:
            attribute_points_awarded = level_ups * 5
            db.cursor.execute(
                """UPDATE users SET
                       free_attribute_points=COALESCE(free_attribute_points, 0)+?,
                       total_attribute_points_earned=COALESCE(total_attribute_points_earned, 0)+?
                     WHERE user_id=?""",
                (attribute_points_awarded, attribute_points_awarded, user_id),
            )

        db.cursor.execute(
            "UPDATE users SET level=?, exp=? WHERE user_id=?",
            (level, exp, user_id),
        )
        max_hp = get_max_hp(user_id)
        db.cursor.execute(
            "UPDATE users SET max_hp=? WHERE user_id=?",
            (max_hp, user_id),
        )

        reward_result = apply_level_up_rewards_in_transaction(
            db, user_id, old_level, level
        )
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise

    return {
        "old_level": old_level,
        "level": level,
        "exp": exp,
        "exp_to_next": db.get_exp_to_next_level(level),
        "level_ups": level_ups,
        "attribute_points_awarded": attribute_points_awarded,
        "reached_levels": reached_levels,
        "level_up_rewards": reward_result,
        "level_up_reward_message": build_level_up_reward_message(reward_result),
    }

