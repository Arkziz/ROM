from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "9_0_6b_auction_weapon_type_line_format_fix"
TARGET_RELATIVE_PATH = Path("systems") / "auction_house_system.py"


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


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original_text = target.read_text(encoding="utf-8")

    marker = "# ✅ HOTFIX 9.0.6b: AUCTION WEAPON TYPE LINE FORMAT FIX"

    if marker in original_text:
        print("ℹ️ Патч уже застосовано. Пропускаю.")
        return

    backup_path = make_backup(root, target)

    patch_code = r'''

# ==============================
# ✅ HOTFIX 9.0.6b: AUCTION WEAPON TYPE LINE FORMAT FIX
# ==============================

def _auction_inventory_style_weapon_type_line(snapshot):
    """
    Формує рядок типу зброї для картки лота Торгового Дому.

    Важливо:
    попередній compatibility-alias міг помилково передавати весь snapshot
    у generic type formatter, через що в картці лота з'являвся рядок типу:

    🧰 Тип: {'durability_current': 100, ...}

    Правильна поведінка:
    - для зброї показати:
      ✋ Тип зброї: одноручна / дворучна
    - для броні, біжутерії, матеріалів, зілля — не показувати нічого.
    """

    if not isinstance(snapshot, dict):
        return ""

    item_type = str(
        snapshot.get("item_type")
        or snapshot.get("type")
        or snapshot.get("item_category")
        or ""
    )

    slot_key = str(
        snapshot.get("slot_key")
        or snapshot.get("item_slot")
        or snapshot.get("item_slot_key")
        or ""
    )

    row = snapshot.get("row") or {}

    if isinstance(row, dict):
        item_type = item_type or str(row.get("item_type") or "")
        slot_key = slot_key or str(row.get("item_slot_key") or "")

    weapon_min_damage = int(snapshot.get("weapon_min_damage", 0) or 0)
    weapon_max_damage = int(snapshot.get("weapon_max_damage", 0) or 0)
    weapon_min_magic_damage = int(snapshot.get("weapon_min_magic_damage", 0) or 0)
    weapon_max_magic_damage = int(snapshot.get("weapon_max_magic_damage", 0) or 0)

    if isinstance(row, dict):
        weapon_min_damage = weapon_min_damage or int(row.get("item_weapon_min_damage", 0) or 0)
        weapon_max_damage = weapon_max_damage or int(row.get("item_weapon_max_damage", 0) or 0)
        weapon_min_magic_damage = weapon_min_magic_damage or int(row.get("item_weapon_min_magic_damage", 0) or 0)
        weapon_max_magic_damage = weapon_max_magic_damage or int(row.get("item_weapon_max_magic_damage", 0) or 0)

    is_weapon = (
        item_type == "weapon"
        or slot_key == "main_hand"
        or weapon_min_damage > 0
        or weapon_max_damage > 0
        or weapon_min_magic_damage > 0
        or weapon_max_magic_damage > 0
    )

    if not is_weapon:
        return ""

    weapon_hands = snapshot.get("weapon_hands")

    if weapon_hands is None and isinstance(row, dict):
        weapon_hands = row.get("item_weapon_hands")

    try:
        weapon_hands = int(weapon_hands or 1)
    except Exception:
        weapon_hands = 1

    if weapon_hands >= 2:
        weapon_type_label = "дворучна"
    else:
        weapon_type_label = "одноручна"

    return f"✋ Тип зброї: {weapon_type_label}"
'''

    new_text = original_text.rstrip() + "\n" + patch_code + "\n"

    target.write_text(new_text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original_text, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після патча.\n"
            "Файл відновлено з backup-копії.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.6b застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ systems/auction_house_system.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- у картці лота більше не має показуватися snapshot-словник")
    print("- для зброї показується: ✋ Тип зброї: одноручна / дворучна")
    print("- для броні цей рядок не показується")


if __name__ == "__main__":
    main()