from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "death_hp_to_1"
TARGET_RELATIVE_PATH = Path("handlers") / "combat.py"


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH
    backup_dir = root / "backup"

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            f"Запускай патч із ROM або з ROM\\patch."
        )

    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"handlers_combat_{PATCH_NAME}_{timestamp}.py"

    original_text = target.read_text(encoding="utf-8")
    backup_path.write_text(original_text, encoding="utf-8")

    text = original_text

    # ==============================
    # 1. Після смерті ставимо HP = 1
    # ==============================

    old_hp_line = "set_current_hp(user_id, player_max_hp)"
    new_hp_line = "set_current_hp(user_id, 1)"

    hp_replacements = text.count(old_hp_line)

    if hp_replacements <= 0:
        raise SystemExit(
            "❌ У handlers/combat.py не знайдено рядок:\n"
            f"{old_hp_line}\n\n"
            "Можливо, код смерті вже змінений або має інший формат."
        )

    text = text.replace(old_hp_line, new_hp_line)

    # ==============================
    # 2. Оновлюємо текст смерті
    # ==============================

    old_death_text = "❤️ Здоров’я відновлено\\n"
    new_death_text = "❤️ Після поразки у тебе залишилось 1 HP\\n"

    death_text_replacements = text.count(old_death_text)

    if death_text_replacements > 0:
        text = text.replace(old_death_text, new_death_text)
    else:
        print(
            "⚠️ Текст '❤️ Здоров’я відновлено' не знайдено. "
            "Можливо, він уже змінений. Пропускаю заміну тексту."
        )

    target.write_text(text, encoding="utf-8")

    # ==============================
    # 3. Перевірка синтаксису
    # ==============================

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original_text, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після патча.\n"
            "Файл handlers/combat.py відновлено з backup-копії.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч застосовано успішно.")
    print(f"✅ Backup створено: {backup_path}")
    print(f"✅ Замінено death HP рядків: {hp_replacements}")

    if death_text_replacements > 0:
        print(f"✅ Оновлено текст смерті: {death_text_replacements}")

    print("✅ handlers/combat.py успішно пройшов py_compile.")
    print("")
    print("Тепер після смерті герой матиме 1 HP, а не повне здоров’я.")


if __name__ == "__main__":
    main()