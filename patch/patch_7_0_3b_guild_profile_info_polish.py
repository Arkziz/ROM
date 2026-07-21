from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_3b_guild_profile_info_polish"
DB_MARKER = "# ✅ GUILD PROFILE DISPLAY HELPERS V1"
GUILD_MARKER = "# ✅ GUILD INFO TEXT POLISH V1"
PROFILE_MARKER = "# ✅ PROFILE GUILD LINE V1"

DB_APPEND_CODE = r'''

# ==============================
# ✅ GUILD PROFILE DISPLAY HELPERS V1
# ==============================

# 7.0.3b
# Helper-и для відображення гільдії у профілі персонажа.


def get_user_guild_profile_line(user_id):
    """
    Рядок для профілю персонажа.

    Формат:
    🏰 Гільдія: 🍒 [ВВП]

    Якщо гравець не має гільдії:
    🏰 Гільдія: немає
    """

    try:
        guild = get_user_guild(user_id)
    except Exception:
        guild = None

    if not guild:
        return "🏰 Гільдія: немає\n"

    try:
        icon = guild["icon"] or "🏰"
        tag = guild["tag"] or "???"
    except Exception:
        try:
            icon = guild[3] or "🏰"
            tag = guild[3] or "???"
        except Exception:
            icon = "🏰"
            tag = "???"

    return f"🏰 Гільдія: {icon} [{tag}]\n"
'''

GUILD_APPEND_CODE = r'''

# ==============================
# ✅ GUILD INFO TEXT POLISH V1
# ==============================

# 7.0.3b
# Красивіше відображення інформації про гільдію:
# - Голова: character_name замість user_id
# - Дата створення: DD.MM.YYYY без часу


def _guild_get_character_name_by_user_id(user_id):
    try:
        from db import cursor
        cursor.execute("SELECT character_name FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        if not row:
            return f"user_id={user_id}"

        try:
            return row["character_name"] or f"user_id={user_id}"
        except Exception:
            return row[0] or f"user_id={user_id}"

    except Exception:
        return f"user_id={user_id}"


def _guild_format_ua_date(value):
    value = str(value or "").strip()

    if not value:
        return "невідомо"

    # ISO: 2026-07-21T14:35:43.161900 -> 21.07.2026
    try:
        date_part = value.split("T", 1)[0].split(" ", 1)[0]
        year, month, day = date_part.split("-", 2)
        return f"{day}.{month}.{year}"
    except Exception:
        return value


def build_guild_info_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    guild_name = get_guild_display_name(guild)
    member_count = get_guild_member_count(guild["id"])
    season_key = get_current_guild_season_key()
    leader_name = _guild_get_character_name_by_user_id(guild["leader_user_id"])
    created_at = _guild_format_ua_date(guild["created_at"])

    return (
        f"ℹ️ Інформація про гільдію\n\n"
        f"{guild_name}\n"
        f"Голова: {leader_name}\n"
        f"Рівень: {guild['level']}\n"
        f"Учасники: {member_count}/{guild['member_limit']}\n"
        f"Створено: {created_at}\n\n"
        f"Поточний сезон: {season_key}\n"
        f"Місячний score: {guild['monthly_score']}\n"
        f"All-time score: {guild['total_score']}"
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


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")
    if DB_MARKER in original:
        print("ℹ️ db.py: guild profile helpers уже є.")
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + DB_APPEND_CODE + "\n", encoding="utf-8")
    print("✅ db.py: додано get_user_guild_profile_line().")
    return target, backup, original, True


def patch_guild_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")

    original = target.read_text(encoding="utf-8")
    if GUILD_MARKER in original:
        print("ℹ️ handlers/guild.py: polish уже є.")
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + GUILD_APPEND_CODE + "\n", encoding="utf-8")
    print("✅ handlers/guild.py: додано красивий build_guild_info_text().")
    return target, backup, original, True


def file_contains_profile_text(text):
    return ("📝 Ім" in text or "📝 Ім'" in text) and "🧭 Клас" in text


def patch_profile_file(path):
    original = path.read_text(encoding="utf-8")

    if PROFILE_MARKER in original or "get_user_guild_profile_line" in original:
        return None, original, False, "already"

    if not file_contains_profile_text(original):
        return None, original, False, "not_profile"

    backup = make_backup(path.parents[1] if path.parent.name == "handlers" else path.parent, path)
    text = original

    # Add import. A standalone import is safe even if there is already a from db import (...).
    text = "from db import get_user_guild_profile_line\n" + text

    lines = text.splitlines(True)
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)

        if not inserted and "📝 Ім" in line and "\\n" in line:
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f'{indent}f"{{get_user_guild_profile_line(user_id)}}"\n')
            new_lines.append(f'{indent}# ✅ PROFILE GUILD LINE V1\n')
            inserted = True

    if not inserted:
        # Rollback this file if we cannot safely insert.
        path.write_text(original, encoding="utf-8")
        return backup, original, False, "no_anchor"

    path.write_text("".join(new_lines), encoding="utf-8")
    return backup, original, True, "patched"


def patch_profile_display(root):
    candidates = []

    for folder in [root / "handlers", root]:
        if not folder.exists():
            continue
        for path in folder.glob("*.py"):
            if path.name.startswith("patch_"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if file_contains_profile_text(text):
                candidates.append(path)

    results = []

    for path in candidates:
        backup, original, changed, status = patch_profile_file(path)
        results.append((path, backup, original, changed, status))

    return results


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_db, patch_guild_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        profile_results = patch_profile_display(root)

        profile_patched = False
        for path, backup, original, changed, status in profile_results:
            print(f"ℹ️ profile scan: {path} -> {status}")
            if changed:
                profile_patched = True
                changed_files.append(path)
                originals.append((path, original))
            if backup:
                backups.append(backup)

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_3b_guild_profile_info_polish.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("\n✅ Патч 7.0.3b Guild profile/info polish застосовано успішно.")
    print("\nЗмінені файли:")
    for file_path in changed_files:
        print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо зроблено:")
    print("- у профіль персонажа додано рядок 🏰 Гільдія: іконка [TAG], якщо знайдено profile-файл")
    print("- у профілі для гравця без гільдії буде 🏰 Гільдія: немає")
    print("- у інформації про гільдію Голова показується як імʼя персонажа")
    print("- дата створення гільдії показується у форматі DD.MM.YYYY")

    if not any(result[3] for result in profile_results):
        print("\n⚠️ Профільний файл не вдалося пропатчити автоматично.")
        print("Надішли актуальний handlers/profile.py або файл, де формується 👤 Персонаж, і я дам точний патч.")

    print("\nПісля патча:")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
