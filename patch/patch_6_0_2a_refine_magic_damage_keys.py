from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_2a_refine_magic_damage_keys"
DB_MARKER = "# ✅ REFINE EFFECTS V1 HOTFIX: MAGIC/PHYSICAL DAMAGE KEYS"

DB_APPEND_CODE = r'''

# ==============================
# ✅ REFINE EFFECTS V1 HOTFIX: MAGIC/PHYSICAL DAMAGE KEYS
# ==============================

# 6.0.2a
# Виправляє випадок, коли get_weapon_damage_by_inventory_id() повертає dict з ключами:
# - physical_min / physical_max
# - magic_min / magic_max
# Старий 6.0.2 обробляв інші назви ключів, тому магічна шкода посоха/жезла могла не збільшуватись.

try:
    _base_get_weapon_damage_for_refine_hotfix_v1 = _base_get_weapon_damage_by_inventory_id_before_refine_v1
except Exception:
    try:
        _base_get_weapon_damage_for_refine_hotfix_v1 = get_weapon_damage_by_inventory_id
    except Exception:
        _base_get_weapon_damage_for_refine_hotfix_v1 = None


def _build_refined_weapon_damage_text(damage_data):
    attack_type = damage_data.get("attack_type", "")

    physical_min = int(damage_data.get("physical_min", 0) or 0)
    physical_max = int(damage_data.get("physical_max", 0) or 0)
    magic_min = int(damage_data.get("magic_min", 0) or 0)
    magic_max = int(damage_data.get("magic_max", 0) or 0)

    if attack_type == "magical" or magic_min > 0 or magic_max > 0:
        return f"🔮 Маг. шкода: {magic_min}-{magic_max}"

    if attack_type == "physical" or physical_min > 0 or physical_max > 0:
        return f"⚔️ Фіз. шкода: {physical_min}-{physical_max}"

    return damage_data.get("text", "")


def _apply_refine_to_weapon_damage_result_v2(base_result, refine_level):
    from systems.refine_system import apply_weapon_refine_to_damage

    try:
        refine_level = int(refine_level or 0)
    except Exception:
        refine_level = 0

    if refine_level <= 0:
        return base_result

    if isinstance(base_result, dict):
        result = dict(base_result)

        key_pairs = [
            ("physical_min", "physical_max"),
            ("magic_min", "magic_max"),
            ("weapon_min_damage", "weapon_max_damage"),
            ("weapon_min_magic_damage", "weapon_max_magic_damage"),
            ("min_damage", "max_damage"),
            ("min_magic_damage", "max_magic_damage"),
        ]

        for min_key, max_key in key_pairs:
            if min_key not in result or max_key not in result:
                continue

            min_damage = int(result.get(min_key, 0) or 0)
            max_damage = int(result.get(max_key, 0) or 0)

            if min_damage <= 0 and max_damage <= 0:
                continue

            refined_min, refined_max = apply_weapon_refine_to_damage(
                min_damage=min_damage,
                max_damage=max_damage,
                refine_level=refine_level,
            )

            result[min_key] = refined_min
            result[max_key] = refined_max

        result["refine_level"] = refine_level
        result["refine_applied"] = True
        result["text"] = _build_refined_weapon_damage_text(result)

        return result

    if isinstance(base_result, (tuple, list)):
        values = list(base_result)

        if len(values) >= 2:
            min_damage = int(values[0] or 0)
            max_damage = int(values[1] or 0)

            if min_damage > 0 or max_damage > 0:
                values[0], values[1] = apply_weapon_refine_to_damage(
                    min_damage=min_damage,
                    max_damage=max_damage,
                    refine_level=refine_level,
                )

        if len(values) >= 4:
            min_magic = int(values[2] or 0)
            max_magic = int(values[3] or 0)

            if min_magic > 0 or max_magic > 0:
                values[2], values[3] = apply_weapon_refine_to_damage(
                    min_damage=min_magic,
                    max_damage=max_magic,
                    refine_level=refine_level,
                )

        if isinstance(base_result, tuple):
            return tuple(values)

        return values

    return base_result


def get_weapon_damage_by_inventory_id(inventory_id):
    """
    FINAL HOTFIX OVERRIDE:
    weapon damage з урахуванням refine_level для актуального формату dict:
    - physical_min / physical_max
    - magic_min / magic_max
    """

    if _base_get_weapon_damage_for_refine_hotfix_v1 is None:
        return None

    base_result = _base_get_weapon_damage_for_refine_hotfix_v1(inventory_id)

    try:
        refine_level = get_inventory_refine_level(inventory_id)
    except Exception:
        refine_level = 0

    return _apply_refine_to_weapon_damage_result_v2(
        base_result=base_result,
        refine_level=refine_level,
    )
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / "db.py"

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py. Запускай патч з кореня ROM або з ROM\\patch.")

    original = target.read_text(encoding="utf-8")

    if DB_MARKER in original:
        print("ℹ️ db.py: hotfix 6.0.2a вже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + DB_APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_2a_refine_magic_damage_keys.\n"
            "db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.2a застосовано успішно.")
    print("✅ db.py пройшов py_compile.")
    print(f"✅ Backup: {backup_path}")
    print("")
    print("Що виправлено:")
    print("- refine тепер множить magic_min/magic_max")
    print("- refine тепер множить physical_min/physical_max")
    print("- текст шкоди оновлюється після множника")


if __name__ == "__main__":
    main()
