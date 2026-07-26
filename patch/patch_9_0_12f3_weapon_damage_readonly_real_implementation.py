from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_12f3_weapon_damage_readonly_real_implementation"
TARGET_RELATIVE_PATH = Path("systems") / "equipment_system.py"
SMOKE_RELATIVE_PATH = Path("tools") / "smoke_test_weapon_damage_contracts.py"
MARKER = "# ROM 9.0.12f3 WEAPON DAMAGE READ-ONLY REAL IMPLEMENTATION"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe}_{PATCH_NAME}_{stamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def build_equipment_code():
    return r'''

# ==============================
# ROM 9.0.12f3 WEAPON DAMAGE READ-ONLY REAL IMPLEMENTATION
# ==============================

_WEAPON_DAMAGE_RARITY_MULTIPLIERS_V4 = {
    "common": 1.00,
    "uncommon": 1.35,
    "rare": 1.85,
    "epic": 2.60,
}

_MAGICAL_WEAPON_SUBTYPES_V4 = {
    "wand_1h",
    "staff_2h",
    "wand",
    "staff",
}


def _weapon_damage_db_v4():
    import db as _db_module
    return _db_module


def _weapon_damage_table_columns_v4(table_name):
    db = _weapon_damage_db_v4()
    try:
        rows = db.conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row[1]) for row in rows}
    except Exception:
        return set()


def init_weapon_damage_system():
    db = _weapon_damage_db_v4()
    columns = _weapon_damage_table_columns_v4("items")
    migrations = (
        ("weapon_min_damage", "INTEGER DEFAULT 0"),
        ("weapon_max_damage", "INTEGER DEFAULT 0"),
        ("weapon_min_magic_damage", "INTEGER DEFAULT 0"),
        ("weapon_max_magic_damage", "INTEGER DEFAULT 0"),
        ("weapon_attack_type", "TEXT DEFAULT ''"),
        ("item_subtype", "TEXT DEFAULT ''"),
    )
    for column, column_type in migrations:
        if column in columns:
            continue
        try:
            db.conn.execute(f"ALTER TABLE items ADD COLUMN {column} {column_type}")
        except Exception:
            pass
    db.conn.commit()
    return True


def calculate_weapon_damage_by_values(item_level, rarity, weapon_hands=1):
    """Preserve the current base formula: level x 0.8/1.2 x rarity x hands."""
    try:
        level = max(1, int(item_level or 1))
    except Exception:
        level = 1
    rarity_key = str(rarity or "common").strip().lower()
    rarity_multiplier = _WEAPON_DAMAGE_RARITY_MULTIPLIERS_V4.get(rarity_key, 1.0)
    try:
        hand_multiplier = 1.35 if int(weapon_hands or 1) == 2 else 1.0
    except Exception:
        hand_multiplier = 1.0
    minimum = max(1, int(round(level * 0.8 * rarity_multiplier * hand_multiplier)))
    maximum = max(minimum, int(round(level * 1.2 * rarity_multiplier * hand_multiplier)))
    return minimum, maximum


def _weapon_damage_empty_result_v4():
    return {
        "is_weapon": False,
        "attack_type": "physical",
        "physical_min": 0,
        "physical_max": 0,
        "magic_min": 0,
        "magic_max": 0,
        "text": None,
    }


def _weapon_is_magical_v4(name, item_subtype, weapon_attack_type):
    attack_type = str(weapon_attack_type or "").strip().lower()
    if attack_type in {"magical", "magic"}:
        return True
    subtype = str(item_subtype or "").strip().lower()
    if subtype in _MAGICAL_WEAPON_SUBTYPES_V4:
        return True
    lowered_name = str(name or "").lower()
    return "посох" in lowered_name or "жезл" in lowered_name or "wand" in lowered_name or "staff" in lowered_name


def _weapon_damage_apply_refine_v4(minimum, maximum, refine_level):
    try:
        from systems.refine_system import apply_weapon_refine_to_damage
        return apply_weapon_refine_to_damage(minimum, maximum, refine_level)
    except Exception:
        return int(minimum or 0), int(maximum or 0)


def get_weapon_damage_by_inventory_id(inventory_id):
    """Return the established weapon-damage dict, including refine multiplier."""
    init_weapon_damage_system()
    db = _weapon_damage_db_v4()
    row = db.conn.execute(
        "SELECT it.name, it.category, it.slot_key, COALESCE(it.weapon_hands,1), "
        "it.rarity, COALESCE(it.item_level,1), "
        "COALESCE(it.weapon_min_damage,0), COALESCE(it.weapon_max_damage,0), "
        "COALESCE(it.weapon_min_magic_damage,0), COALESCE(it.weapon_max_magic_damage,0), "
        "COALESCE(it.weapon_attack_type,''), COALESCE(it.item_subtype,''), "
        "COALESCE(inv.refine_level,0) "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (int(inventory_id),),
    ).fetchone()
    if not row:
        return _weapon_damage_empty_result_v4()

    (
        name, category, slot_key, weapon_hands, rarity, item_level,
        physical_min, physical_max, magic_min, magic_max,
        weapon_attack_type, item_subtype, refine_level,
    ) = row

    if category != "equipment" or slot_key != "main_hand":
        return _weapon_damage_empty_result_v4()

    is_magical = _weapon_is_magical_v4(name, item_subtype, weapon_attack_type)
    attack_type = "magical" if is_magical else "physical"

    if is_magical:
        base_min = int(magic_min or 0)
        base_max = int(magic_max or 0)
        if base_min <= 0 or base_max <= 0:
            base_min, base_max = calculate_weapon_damage_by_values(item_level, rarity, weapon_hands)
        final_min, final_max = _weapon_damage_apply_refine_v4(base_min, base_max, refine_level)
        return {
            "is_weapon": True,
            "attack_type": attack_type,
            "physical_min": 0,
            "physical_max": 0,
            "magic_min": final_min,
            "magic_max": final_max,
            "text": f"🔮 Маг. шкода: {final_min}-{final_max}",
        }

    base_min = int(physical_min or 0)
    base_max = int(physical_max or 0)
    if base_min <= 0 or base_max <= 0:
        base_min, base_max = calculate_weapon_damage_by_values(item_level, rarity, weapon_hands)
    final_min, final_max = _weapon_damage_apply_refine_v4(base_min, base_max, refine_level)
    return {
        "is_weapon": True,
        "attack_type": attack_type,
        "physical_min": final_min,
        "physical_max": final_max,
        "magic_min": 0,
        "magic_max": 0,
        "text": f"⚔️ Шкода: {final_min}-{final_max}",
    }


def get_inventory_weapon_damage_display(inventory_id):
    result = get_weapon_damage_by_inventory_id(inventory_id)
    if not isinstance(result, dict) or not result.get("is_weapon"):
        return None
    return result.get("text")
'''


def build_smoke_test():
    return r'''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from systems.refine_system import apply_weapon_refine_to_damage

USER_ID = 243129101


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    base_1h = db.calculate_weapon_damage_by_values(8, "common", 1)
    base_2h = db.calculate_weapon_damage_by_values(8, "common", 2)
    require(base_1h == (6, 10), f"unexpected 1H formula result: {base_1h}")
    require(base_2h == (9, 13), f"unexpected 2H formula result: {base_2h}")

    row = db.conn.execute(
        "SELECT es.inventory_id FROM equipment_slots es "
        "WHERE es.user_id=? AND es.slot_key='main_hand'",
        (USER_ID,),
    ).fetchone()
    if not row or row[0] is None:
        print("[OK] weapon damage formula contracts")
        print("- no equipped main-hand weapon for runtime item check")
        return 0

    inventory_id = int(row[0])
    result = db.get_weapon_damage_by_inventory_id(inventory_id)
    display = db.get_inventory_weapon_damage_display(inventory_id)
    refine_level = db.get_inventory_refine_level(inventory_id)

    require(isinstance(result, dict), type(result))
    required_keys = {
        "is_weapon", "attack_type", "physical_min", "physical_max",
        "magic_min", "magic_max", "text",
    }
    require(required_keys.issubset(result), f"missing keys: {required_keys - set(result)}")
    require(result["is_weapon"] is True, result)
    require(result["attack_type"] in {"physical", "magical"}, result)
    require(isinstance(display, str) and display == result["text"], (display, result))

    raw = db.conn.execute(
        "SELECT COALESCE(it.weapon_min_damage,0), COALESCE(it.weapon_max_damage,0), "
        "COALESCE(it.weapon_min_magic_damage,0), COALESCE(it.weapon_max_magic_damage,0), "
        "COALESCE(it.item_level,1), it.rarity, COALESCE(it.weapon_hands,1) "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (inventory_id,),
    ).fetchone()

    if result["attack_type"] == "magical":
        base_min, base_max = int(raw[2] or 0), int(raw[3] or 0)
        actual = (result["magic_min"], result["magic_max"])
    else:
        base_min, base_max = int(raw[0] or 0), int(raw[1] or 0)
        actual = (result["physical_min"], result["physical_max"])
    if base_min <= 0 or base_max <= 0:
        base_min, base_max = db.calculate_weapon_damage_by_values(raw[4], raw[5], raw[6])
    expected = apply_weapon_refine_to_damage(base_min, base_max, refine_level)
    require(actual == expected, f"refine mismatch: actual={actual}, expected={expected}")

    print("[OK] weapon damage read-only runtime contracts")
    print("- inventory_id:", inventory_id)
    print("- attack_type:", result["attack_type"])
    print("- refine_level:", refine_level)
    print("- base damage:", (base_min, base_max))
    print("- final damage:", actual)
    print("- display:", display)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH
    smoke = root / SMOKE_RELATIVE_PATH
    if not target.exists():
        raise SystemExit(f"Missing file: {target}")

    original = target.read_text(encoding="utf-8")
    original_smoke = smoke.read_text(encoding="utf-8") if smoke.exists() else None
    if MARKER in original:
        print("Patch 9.0.12f3 already applied. Skipping.")
        return

    backups = [make_backup(root, target)]
    if smoke.exists():
        backups.append(make_backup(root, smoke))

    try:
        target.write_text(original.rstrip() + "\n" + build_equipment_code() + "\n", encoding="utf-8")
        smoke.parent.mkdir(exist_ok=True)
        smoke.write_text(build_smoke_test(), encoding="utf-8")
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
        raise SystemExit(f"Patch failed; files restored. Error: {error}")

    print("Patch 9.0.12f3 applied successfully.")
    print("Weapon damage read-only logic now lives in systems/equipment_system.py.")
    print("Backups:")
    for path in backups:
        print(f"- {path}")
    print("Checks:")
    print(r"python -m py_compile .\systems\equipment_system.py")
    print(r"python -m py_compile .\db.py")
    print(r"python tools/check_imports.py")
    print(r"python tools/smoke_test_rom_core.py")
    print(r"python tools/smoke_test_equipment_readonly_core.py")
    print(r"python tools/smoke_test_inventory_refine_contracts.py")
    print(r"python tools/smoke_test_weapon_damage_contracts.py")
    print(r"python tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
