from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_8d_blacksmith_repair_confirmation_final_fix"
CITY_MARKER = "# ✅ ROM 9.0.8d CITY REPAIR CALLBACK FINAL FIX"
MAIN_MARKER = "# ✅ ROM 9.0.8d MAIN REPAIR CONFIRMATION ORDER FIX"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def patch_city(root):
    target = root / "handlers" / "city.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/city.py")

    original = target.read_text(encoding="utf-8")
    if CITY_MARKER in original:
        return target, None, False

    text = original
    changes = 0

    # Саме handlers/city.py генерує ремонтне меню, яке імпортується в blacksmith_repair_hotfix.py.
    replacements = [
        ('callback_data=f"repair_one_{inventory_id}"', 'callback_data=f"repair_prompt_one_v3_{inventory_id}"'),
        ("callback_data=f'repair_one_{inventory_id}'", "callback_data=f'repair_prompt_one_v3_{inventory_id}'"),
        ('callback_data="repair_all_equipped"', 'callback_data="repair_prompt_all_v3"'),
        ("callback_data='repair_all_equipped'", "callback_data='repair_prompt_all_v3'"),
    ]

    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changes += 1

    if changes == 0:
        raise SystemExit(
            "❌ У handlers/city.py не знайдено очікувані callback_data для ремонту.\n"
            "Патч не застосовано, щоб не ламати файл наосліп."
        )

    text = text.rstrip() + "\n\n" + CITY_MARKER + "\n# Repair menu now uses confirmation callbacks: repair_prompt_one_v3_* / repair_prompt_all_v3\n"

    backup = make_backup(root, target)
    target.write_text(text, encoding="utf-8")
    return target, backup, True


def patch_main_order(root):
    target = root / "main.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")
    if MAIN_MARKER in original:
        return target, None, False

    text = original
    backup = make_backup(root, target)

    # Ensure import exists.
    import_line = "from handlers.blacksmith_repair_confirm import register_blacksmith_repair_confirmation_handlers\n"
    if import_line not in text:
        lines = text.splitlines(keepends=True)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith("from handlers.") or line.startswith("import handlers."):
                insert_index = i + 1
        lines.insert(insert_index, import_line)
        text = "".join(lines)

    # Remove all existing direct registration lines and re-insert before hotfix/city.
    registration_line = "register_blacksmith_repair_confirmation_handlers(bot)"
    lines = text.splitlines()
    lines = [line for line in lines if line.strip() != registration_line]

    inserted = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in {
            "register_blacksmith_repair_hotfix_handlers(bot)",
            "register_city_handlers(bot)",
        }:
            indent = line[:len(line) - len(line.lstrip())]
            lines.insert(i, indent + registration_line)
            inserted = True
            break

    if not inserted:
        raise SystemExit(
            "❌ Не вдалося знайти місце для реєстрації register_blacksmith_repair_confirmation_handlers(bot)."
        )

    text = "\n".join(lines) + "\n\n" + MAIN_MARKER + "\n# Repair confirmation handlers are registered before old hotfix/city handlers.\n"
    target.write_text(text, encoding="utf-8")
    return target, backup, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed = []
    backups = []
    originals = []

    try:
        for patcher in [patch_city, patch_main_order]:
            path, backup, did_change = patcher(root)
            if did_change:
                changed.append(path)
                backups.append(backup)

        for rel in ["handlers/city.py", "main.py", "handlers/blacksmith_repair_confirm.py"]:
            path = root / rel
            if path.exists():
                py_compile.compile(str(path), doraise=True)

    except Exception as error:
        raise SystemExit(
            "❌ Помилка під час patch_9_0_8d_blacksmith_repair_confirmation_final_fix.\n"
            "Перевір backup у ROM\\backup, якщо потрібно відкотити.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.8d Blacksmith repair confirmation FINAL fix застосовано успішно.")
    print()
    print("Змінено:")
    for p in changed:
        print(f"- {p}")
    print()
    print("Backup:")
    for b in backups:
        print(f"- {b}")
    print()
    print("Що виправлено:")
    print("- handlers/city.py тепер генерує repair_prompt_one_v3_* замість repair_one_*")
    print("- handlers/city.py тепер генерує repair_prompt_all_v3 замість repair_all_equipped")
    print("- main.py реєструє confirmation handlers перед старими blacksmith/city handlers")
    print("- старі instant repair handlers більше не мають отримувати кліки з меню ремонту")
    print()
    print("Після патча запусти:")
    print("python -m py_compile .\\handlers\\city.py")
    print("python -m py_compile .\\main.py")
    print("python -m py_compile .\\handlers\\blacksmith_repair_confirm.py")
    print("python tools/check_imports.py")
    print("python tools/smoke_test_rom_core.py")


if __name__ == "__main__":
    main()
