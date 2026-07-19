from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_6_refine_stone_drop"
TARGET_RELATIVE_PATH = Path("systems") / "reward_system.py"
MARKER = "# ✅ REFINE STONE DROP V1"

APPEND_CODE = r'''

# ==============================
# ✅ REFINE STONE DROP V1
# ==============================

# 6.0.6
# 🪨 Камінь Посилення падає з мобів.
# 💎 Руна Успіху НЕ падає з мобів — буде за кристали пізніше.

REFINE_STONE_ITEM_ID = 401
NORMAL_REFINE_STONE_DROP_CHANCE = 0.08
ELITE_REFINE_STONE_DROP_CHANCE = 0.20

try:
    _base_roll_loot_before_refine_stone_drop_v1 = roll_loot
except Exception:
    _base_roll_loot_before_refine_stone_drop_v1 = None


def roll_refine_stone_drop(user_id, mob):
    """
    Окремий глобальний roll для 🪨 Каменя Посилення.

    Баланс:
    - звичайний моб: 8%
    - елітний моб: 20%

    💎 Руна Успіху тут НЕ падає.
    """

    is_elite = bool(mob.get("is_elite", False))

    if is_elite:
        chance = ELITE_REFINE_STONE_DROP_CHANCE
    else:
        chance = NORMAL_REFINE_STONE_DROP_CHANCE

    if random.random() > chance:
        return None

    result = add_item(user_id, REFINE_STONE_ITEM_ID, 1)

    if result.get("added", 0) > 0:
        name = result.get("name", "🪨 Камінь Посилення")
        added = result.get("added", 1)
        return f"{name} x{added}"

    if result.get("lost", 0) > 0:
        name = result.get("name", "🪨 Камінь Посилення")
        lost = result.get("lost", 1)
        return f"⚠️ Не влізло в сумку: {name} x{lost}"

    return None


def roll_loot(user_id, mob):
    """
    FINAL OVERRIDE:
    Додає шанс дропу 🪨 Каменя Посилення до вже існуючого луту.
    """

    if _base_roll_loot_before_refine_stone_drop_v1 is not None:
        messages = _base_roll_loot_before_refine_stone_drop_v1(user_id, mob)
    else:
        messages = []

    if messages is None:
        messages = []

    stone_message = roll_refine_stone_drop(user_id, mob)

    if stone_message:
        messages.append(stone_message)

    return messages
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


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Запускай патч із ROM або з ROM\\patch."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ REFINE STONE DROP V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)

    updated = original.rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_6_refine_stone_drop.\n"
            "systems/reward_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.6 Refine Stone Drop застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ systems/reward_system.py пройшов py_compile.")
    print("")
    print("Додано дроп:")
    print("- 🪨 Камінь Посилення зі звичайного моба: 8%")
    print("- 🪨 Камінь Посилення з елітного моба: 20%")
    print("- 💎 Руна Успіху НЕ падає з мобів")


if __name__ == "__main__":
    main()
