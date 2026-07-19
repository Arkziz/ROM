from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_2_refine_effects"
DB_MARKER = "# ✅ REFINE EFFECTS V1"

DB_APPEND_CODE = r'''

# ==============================
# ✅ REFINE EFFECTS V1
# ==============================

# 6.0.2
# Підключення заточки до реальних параметрів:
# - зброя: refine_level збільшує weapon damage;
# - броня: refine_level додає % до max HP;
# - PDEF/MDEF/STR/DEX/INT/WIS заточка НЕ змінює.

try:
    _base_get_max_hp_before_refine_v1 = get_max_hp
except Exception:
    _base_get_max_hp_before_refine_v1 = None

try:
    _base_get_weapon_damage_by_inventory_id_before_refine_v1 = get_weapon_damage_by_inventory_id
except Exception:
    _base_get_weapon_damage_by_inventory_id_before_refine_v1 = None


def get_refine_total_armor_hp_bonus_percent(user_id):
    """
    Повертає сумарний HP% бонус від заточеної броні.

    За ТЗ:
    - броня точиться до +6;
    - броня збільшує тільки максимальний HP;
    - PDEF/MDEF і характеристики не змінюються.
    """

    from systems.refine_system import get_armor_refine_hp_bonus_percent

    init_refine_system()
    ensure_equipment_slots(user_id)

    armor_slots = {
        "helmet",
        "shoulders",
        "chest",
        "gloves",
        "legs",
        "boots",
    }

    equipped_slots = get_all_equipped_slots(user_id)
    total_bonus = 0.0

    for slot_key, inventory_id in equipped_slots.items():
        if slot_key not in armor_slots:
            continue

        if not inventory_id:
            continue

        cursor.execute("""
        SELECT
            inventory.refine_level,
            items.rarity
        FROM inventory
        JOIN items ON inventory.item_id = items.id
        WHERE inventory.id=? AND inventory.user_id=?
        """, (inventory_id, user_id))

        row = cursor.fetchone()

        if not row:
            continue

        refine_level, rarity = row

        try:
            refine_level = int(refine_level or 0)
        except Exception:
            refine_level = 0

        if refine_level <= 0:
            continue

        total_bonus += float(
            get_armor_refine_hp_bonus_percent(
                refine_level=refine_level,
                rarity=rarity
            )
        )

    return round(total_bonus, 2)


def get_max_hp(user_id):
    """
    FINAL OVERRIDE:
    max HP з урахуванням refine броні.

    Формула за ТЗ:
    Final HP = Base HP × (1 + Total_HP_Bonus / 100)

    Важливо:
    Base HP рахується старою функцією get_max_hp().
    Refine броні не змінює STA/PDEF/MDEF, а додає тільки HP%.
    """

    if _base_get_max_hp_before_refine_v1 is None:
        return 1

    base_hp = int(_base_get_max_hp_before_refine_v1(user_id) or 1)

    if base_hp <= 0:
        base_hp = 1

    total_bonus = get_refine_total_armor_hp_bonus_percent(user_id)

    if total_bonus <= 0:
        return base_hp

    final_hp = int(round(base_hp * (1 + total_bonus / 100)))

    return max(1, final_hp)


def _apply_refine_multiplier_to_damage_dict(damage_data, refine_level):
    """
    Підтримує різні можливі формати dict з damage-полями.
    """

    from systems.refine_system import apply_weapon_refine_to_damage

    if not isinstance(damage_data, dict):
        return damage_data

    result = dict(damage_data)

    damage_pairs = [
        ("weapon_min_damage", "weapon_max_damage"),
        ("min_damage", "max_damage"),
        ("physical_min_damage", "physical_max_damage"),
        ("weapon_min_magic_damage", "weapon_max_magic_damage"),
        ("min_magic_damage", "max_magic_damage"),
        ("magic_min_damage", "magic_max_damage"),
    ]

    for min_key, max_key in damage_pairs:
        if min_key in result and max_key in result:
            min_damage = int(result.get(min_key, 0) or 0)
            max_damage = int(result.get(max_key, 0) or 0)

            if min_damage > 0 or max_damage > 0:
                refined_min, refined_max = apply_weapon_refine_to_damage(
                    min_damage=min_damage,
                    max_damage=max_damage,
                    refine_level=refine_level
                )

                result[min_key] = refined_min
                result[max_key] = refined_max

    result["refine_level"] = refine_level
    result["refine_applied"] = True

    return result


def _apply_refine_multiplier_to_damage_sequence(damage_data, refine_level):
    """
    Обережна підтримка tuple/list форматів:
    - (min, max)
    - (min_phys, max_phys, min_magic, max_magic)
    """

    from systems.refine_system import apply_weapon_refine_to_damage

    if not isinstance(damage_data, (tuple, list)):
        return damage_data

    values = list(damage_data)

    if len(values) >= 2:
        min_damage = int(values[0] or 0)
        max_damage = int(values[1] or 0)

        if min_damage > 0 or max_damage > 0:
            values[0], values[1] = apply_weapon_refine_to_damage(
                min_damage=min_damage,
                max_damage=max_damage,
                refine_level=refine_level
            )

    if len(values) >= 4:
        min_magic = int(values[2] or 0)
        max_magic = int(values[3] or 0)

        if min_magic > 0 or max_magic > 0:
            values[2], values[3] = apply_weapon_refine_to_damage(
                min_damage=min_magic,
                max_damage=max_magic,
                refine_level=refine_level
            )

    if isinstance(damage_data, tuple):
        return tuple(values)

    return values


def get_weapon_damage_by_inventory_id(inventory_id):
    """
    FINAL OVERRIDE:
    weapon damage з урахуванням refine_level.

    За ТЗ:
    Final Min Damage = Base Min Damage × Refine Multiplier
    Final Max Damage = Base Max Damage × Refine Multiplier
    """

    if _base_get_weapon_damage_by_inventory_id_before_refine_v1 is None:
        return None

    base_result = _base_get_weapon_damage_by_inventory_id_before_refine_v1(inventory_id)

    try:
        refine_level = get_inventory_refine_level(inventory_id)
    except Exception:
        refine_level = 0

    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0

    if refine_level <= 0:
        return base_result

    if isinstance(base_result, dict):
        return _apply_refine_multiplier_to_damage_dict(base_result, refine_level)

    if isinstance(base_result, (tuple, list)):
        return _apply_refine_multiplier_to_damage_sequence(base_result, refine_level)

    return base_result


def get_refine_effects_summary_for_user(user_id):
    """
    Діагностичний helper для тестів.
    """

    return {
        "armor_hp_bonus_percent": get_refine_total_armor_hp_bonus_percent(user_id),
        "max_hp": get_max_hp(user_id),
    }
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(
        target.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


def patch_db(root):
    target = root / "db.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py. Запускай патч з кореня ROM або з ROM\\patch.")

    original = target.read_text(encoding="utf-8")

    if DB_MARKER in original:
        print("ℹ️ db.py: REFINE EFFECTS V1 уже є, пропускаю додавання.")
        return target, None, original

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + DB_APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    return target, backup_path, original


def main():
    root = Path(__file__).resolve().parents[1]

    db_path = root / "db.py"
    target, backup_path, original = patch_db(root)

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_2_refine_effects.\n"
            "db.py відновлено з попереднього стану.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.2 Refine Effects застосовано успішно.")
    print("✅ db.py пройшов py_compile.")

    if backup_path:
        print(f"✅ Backup: {backup_path}")

    print("")
    print("Що підключено:")
    print("- refine_level зброї множить weapon damage")
    print("- refine_level броні додає сумарний HP% до get_max_hp")
    print("- PDEF/MDEF/STR/DEX/INT/WIS заточкою не змінюються")
    print("")
    print("Рекомендована перевірка:")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\systems\\refine_system.py")
    print("")
    print("Наступний етап: 6.0.3/6.0.4 — відображення refine [+N] і UI Коваля.")


if __name__ == "__main__":
    main()
