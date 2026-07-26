from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12g_player_combat_stats_real_implementation"
TARGET = Path("systems") / "player_system.py"
SMOKE = Path("tools") / "smoke_test_player_combat_stats.py"
MARKER = "# ROM 9.0.12g PLAYER COMBAT STATS REAL IMPLEMENTATION"


def backup(root, path):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(path.relative_to(root)).replace("\\", "_").replace("/", "_")
    dst = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    dst.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def implementation():
    return r'''

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
        "SELECT COALESCE(str,0), COALESCE(dex,0), COALESCE(intelligence,0), "
        "COALESCE(wis,0), COALESCE(sta,0), COALESCE(level,1) "
        "FROM users WHERE user_id=?",
        (int(user_id),),
    ).fetchone()


def get_player_stats(user_id: int):
    """Return (STR, DEX, INT, WIS, STA, level), including active equipment."""
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
    return (
        int(base_str or 0) + int(item_str or 0),
        int(base_dex or 0) + int(item_dex or 0),
        int(base_int or 0) + int(item_int or 0),
        int(base_wis or 0) + int(item_wis or 0),
        int(base_sta or 0) + int(item_sta or 0),
        max(1, int(level or 1)),
    )


def get_attack(user_id: int):
    stats = get_player_stats(user_id)
    return int(stats[0]) if stats else 0


def get_magic_attack(user_id: int):
    stats = get_player_stats(user_id)
    return int(stats[2]) if stats else 0


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
        return 100
    _str, _dex, _int, _wis, total_sta, level = stats
    base_hp = 100 + int(level) * 20 + int(total_sta) * 5
    refine_percent = _armor_refine_hp_bonus_percent_9_0_12g(user_id)
    return max(1, int(round(base_hp * (1.0 + refine_percent / 100.0))))


def get_physical_defense(user_id: int):
    stats = get_player_stats(user_id)
    if not stats:
        return 0
    db = _player_combat_db_9_0_12g()
    item_pdef, _item_mdef = db.get_equipped_item_defenses(int(user_id))
    return int(int(item_pdef or 0) + int(stats[4]) * 0.2)


def get_magic_defense(user_id: int):
    stats = get_player_stats(user_id)
    if not stats:
        return 0
    db = _player_combat_db_9_0_12g()
    _item_pdef, item_mdef = db.get_equipped_item_defenses(int(user_id))
    return int(int(item_mdef or 0) + int(stats[3]))


def get_physical_crit_chance_display(user_id: int):
    stats = get_player_stats(user_id)
    if not stats:
        return 5.0
    chance = 5.0 + ((float(stats[1]) - 10.0) / max(1, int(stats[5]))) * 0.5
    return max(1.0, min(35.0, chance))


def get_magical_crit_chance_display(user_id: int):
    stats = get_player_stats(user_id)
    if not stats:
        return 5.0
    chance = 5.0 + ((float(stats[3]) - 10.0) / max(1, int(stats[5]))) * 0.5
    return max(1.0, min(35.0, chance))


def get_base_dodge_chance_display(user_id: int):
    return 5.0
'''


def smoke_test():
    return r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    before = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()
    require(before is not None, "test user not found")

    stats = db.get_player_stats(USER_ID)
    attack = db.get_attack(USER_ID)
    magic_attack = db.get_magic_attack(USER_ID)
    max_hp = db.get_max_hp(USER_ID)
    pdef = db.get_physical_defense(USER_ID)
    mdef = db.get_magic_defense(USER_ID)
    physical_crit = db.get_physical_crit_chance_display(USER_ID)
    magical_crit = db.get_magical_crit_chance_display(USER_ID)
    dodge = db.get_base_dodge_chance_display(USER_ID)

    after_read = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()

    require(isinstance(stats, tuple) and len(stats) == 6, stats)
    require(all(isinstance(v, int) for v in stats), stats)
    require(attack == stats[0], (attack, stats))
    require(magic_attack == stats[2], (magic_attack, stats))
    require(isinstance(max_hp, int) and max_hp >= 1, max_hp)
    require(isinstance(pdef, int) and pdef >= 0, pdef)
    require(isinstance(mdef, int) and mdef >= 0, mdef)
    require(1.0 <= physical_crit <= 35.0, physical_crit)
    require(1.0 <= magical_crit <= 35.0, magical_crit)
    require(dodge == 5.0, dodge)
    require(tuple(before) == tuple(after_read), "combat-stat reads changed stored HP")

    sync = db.sync_user_max_hp(USER_ID, heal_to_full=False)
    current = db.conn.execute(
        "SELECT hp, max_hp FROM users WHERE user_id=?", (USER_ID,)
    ).fetchone()
    require(isinstance(sync, dict), type(sync))
    require(int(current[1]) == max_hp, (current, max_hp))
    require(int(current[0]) <= max_hp, (current, max_hp))

    print("[OK] player combat stats runtime contracts")
    print("- stats:", stats)
    print("- attack / magic:", attack, "/", magic_attack)
    print("- max HP:", max_hp)
    print("- PDEF / MDEF:", pdef, "/", mdef)
    print("- physical / magical crit:", round(physical_crit, 2), "/", round(magical_crit, 2))
    print("- dodge:", dodge)
    print("- HP after sync:", current[0], "/", current[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET
    smoke = root / SMOKE
    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")
    original_smoke = smoke.read_text(encoding="utf-8") if smoke.exists() else None
    if MARKER in original:
        print("ℹ️ Патч 9.0.12g уже застосовано.")
        return

    backups = [backup(root, target)]
    if smoke.exists():
        backups.append(backup(root, smoke))

    try:
        target.write_text(original.rstrip() + "\n" + implementation() + "\n", encoding="utf-8")
        smoke.parent.mkdir(exist_ok=True)
        smoke.write_text(smoke_test(), encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(smoke), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        if original_smoke is None:
            try:
                smoke.unlink()
            except FileNotFoundError:
                pass
        else:
            smoke.write_text(original_smoke, encoding="utf-8")
        raise SystemExit(f"❌ Патч не застосовано; файли відновлено.\nПомилка: {error}")

    print("✅ Патч 9.0.12g успішно застосовано.")
    print("✅ Бойові характеристики гравця тепер обчислюються у systems/player_system.py.")
    print("✅ Динамічний максимум HP і бонус заточки броні збережено.")
    print("Резервні копії:")
    for path in backups:
        print(f"- {path}")
    print("Перевірки:")
    print(r"python -m py_compile .\systems\player_system.py")
    print(r"python -m py_compile .\db.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")
    print("python tools/smoke_test_equipment_readonly_core.py")
    print("python tools/smoke_test_inventory_refine_contracts.py")
    print("python tools/smoke_test_weapon_damage_contracts.py")
    print("python tools/smoke_test_player_combat_stats.py")
    print("python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
