from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_4a_unique_guild_icon"
GUILD_SYSTEM_MARKER = "# ✅ UNIQUE GUILD ICON CORE V1"
DB_MARKER = "# ✅ UNIQUE GUILD ICON DB WRAPPERS V1"
GUILD_HANDLER_MARKER = "# ✅ UNIQUE GUILD ICON UI VALIDATION V1"

GUILD_SYSTEM_APPEND = r'''

# ==============================
# ✅ UNIQUE GUILD ICON CORE V1
# ==============================

# 7.0.4a
# Іконка гільдії має бути унікальною.
# Якщо в БД вже є дублікати, перша гільдія залишає іконку,
# інші дублікати отримують резервні унікальні іконки.

GUILD_RESERVED_UNIQUE_ICONS = [
    "🏰", "🛡️", "⚔️", "🔥", "🌙", "⭐", "🐺", "🐉", "🍀", "💎",
    "🦅", "🦁", "🐻", "🦊", "🦂", "🦉", "🗡️", "🔱", "🌲", "🌋",
    "❄️", "⚡", "🌟", "🌹", "🍒", "🌊", "☀️", "🌌", "🪓", "🧿",
]


def normalize_guild_icon(value):
    icon = (value or "").strip()
    return icon or "🏰"


def get_guild_by_icon(icon):
    init_guild_system_tables_only()
    icon = normalize_guild_icon(icon)

    cursor.execute("SELECT * FROM guilds WHERE icon=?", (icon,))
    return cursor.fetchone()


def is_guild_icon_taken(icon, exclude_guild_id=None):
    init_guild_system_tables_only()
    icon = normalize_guild_icon(icon)

    if exclude_guild_id is None:
        cursor.execute("SELECT 1 FROM guilds WHERE icon=?", (icon,))
    else:
        cursor.execute("SELECT 1 FROM guilds WHERE icon=? AND id != ?", (icon, exclude_guild_id))

    return cursor.fetchone() is not None


def _get_used_guild_icons():
    cursor.execute("SELECT icon FROM guilds")
    rows = cursor.fetchall()
    used = set()

    for row in rows:
        try:
            icon = row["icon"]
        except Exception:
            icon = row[0]
        if icon:
            used.add(icon)

    return used


def _pick_unique_guild_icon(used_icons, preferred=None):
    preferred = normalize_guild_icon(preferred)

    if preferred and preferred not in used_icons:
        return preferred

    for icon in GUILD_RESERVED_UNIQUE_ICONS:
        if icon not in used_icons:
            return icon

    # Very rare fallback if all reserved icons are used.
    # SQLite UNIQUE only needs unique text; UI validation for new guilds still asks for short emoji.
    counter = 1
    while True:
        candidate = f"🏰{counter}"
        if candidate not in used_icons:
            return candidate
        counter += 1


def make_existing_guild_icons_unique():
    """
    Виправляє вже існуючі дублікати icon у guilds.

    Правило:
    - найстаріша/перша гільдія з конкретною іконкою зберігає її;
    - наступні дублікати отримують резервну унікальну іконку.
    """

    init_guild_system_tables_only()

    cursor.execute("SELECT id, icon, name, tag FROM guilds ORDER BY id ASC")
    rows = cursor.fetchall()

    seen = set()
    used = set()
    changes = []

    for row in rows:
        try:
            guild_id = row["id"]
            icon = normalize_guild_icon(row["icon"])
            name = row["name"]
            tag = row["tag"]
        except Exception:
            guild_id = row[0]
            icon = normalize_guild_icon(row[1])
            name = row[2] if len(row) > 2 else "Гільдія"
            tag = row[3] if len(row) > 3 else "???"

        if icon not in seen and icon not in used:
            seen.add(icon)
            used.add(icon)
            continue

        new_icon = _pick_unique_guild_icon(used)
        used.add(new_icon)

        cursor.execute("UPDATE guilds SET icon=?, updated_at=? WHERE id=?", (new_icon, now_iso(), guild_id))
        changes.append((guild_id, icon, new_icon, name, tag))

    conn.commit()

    for guild_id, old_icon, new_icon, name, tag in changes:
        try:
            add_guild_log(
                guild_id=guild_id,
                event_type="icon_auto_changed",
                text=f"Іконку гільдії [{tag}] {name} автоматично змінено з {old_icon} на {new_icon}, бо іконки гільдій мають бути унікальними."
            )
        except Exception:
            pass

    return changes


def ensure_unique_guild_icon_index():
    """
    Створює UNIQUE index для guilds.icon після очищення дублікатів.
    """

    init_guild_system_tables_only()
    make_existing_guild_icons_unique()

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_guilds_icon_unique ON guilds(icon)")
    conn.commit()

    return True


# Override validation from 7.0.1 with icon uniqueness check.
def validate_guild_create_input(name, tag, icon="🏰"):
    name = (name or "").strip()
    tag = normalize_guild_tag(tag)
    icon = normalize_guild_icon(icon)

    if len(name) < 3:
        return {
            "success": False,
            "message": "❌ Назва гільдії має містити мінімум 3 символи."
        }

    if len(name) > 32:
        return {
            "success": False,
            "message": "❌ Назва гільдії має бути не довша за 32 символи."
        }

    if len(tag) < 2:
        return {
            "success": False,
            "message": "❌ Абревіатура гільдії має містити мінімум 2 символи."
        }

    if len(tag) > 5:
        return {
            "success": False,
            "message": "❌ Абревіатура гільдії має бути не довша за 5 символів."
        }

    existing = get_guild_by_name_or_tag(name)
    if existing:
        return {
            "success": False,
            "message": "❌ Гільдія з такою назвою або абревіатурою вже існує."
        }

    existing_tag = get_guild_by_name_or_tag(tag)
    if existing_tag:
        return {
            "success": False,
            "message": "❌ Гільдія з такою назвою або абревіатурою вже існує."
        }

    if is_guild_icon_taken(icon):
        return {
            "success": False,
            "message": "❌ Така іконка вже використовується іншою гільдією. Обери іншу іконку."
        }

    return {
        "success": True,
        "name": name,
        "tag": tag,
        "icon": icon,
    }


# Ensure uniqueness whenever module is loaded after the patch.
try:
    ensure_unique_guild_icon_index()
except Exception as _guild_icon_unique_error:
    print(f"⚠️ Failed to ensure unique guild icon index: {_guild_icon_unique_error}")
'''

DB_APPEND = r'''

# ==============================
# ✅ UNIQUE GUILD ICON DB WRAPPERS V1
# ==============================

# 7.0.4a wrappers для унікальних іконок гільдій.


def get_guild_by_icon(icon):
    from systems.guild_system import get_guild_by_icon as _get_guild_by_icon
    return _get_guild_by_icon(icon)


def is_guild_icon_taken(icon, exclude_guild_id=None):
    from systems.guild_system import is_guild_icon_taken as _is_guild_icon_taken
    return _is_guild_icon_taken(icon=icon, exclude_guild_id=exclude_guild_id)


def make_existing_guild_icons_unique():
    from systems.guild_system import make_existing_guild_icons_unique as _make_existing_guild_icons_unique
    return _make_existing_guild_icons_unique()


def ensure_unique_guild_icon_index():
    from systems.guild_system import ensure_unique_guild_icon_index as _ensure_unique_guild_icon_index
    return _ensure_unique_guild_icon_index()
'''

GUILD_HANDLER_APPEND = r'''

# ==============================
# ✅ UNIQUE GUILD ICON UI VALIDATION V1
# ==============================

# 7.0.4a
# Override UI icon validation: іконка гільдії має бути унікальна.


def validate_guild_icon_for_ui(icon):
    icon = (icon or "").strip() or "🏰"

    # Telegram emoji may be several codepoints, so only prevent very long text.
    if len(icon) > 4:
        return False, "❌ Іконка має бути короткою. Найкраще — один emoji."

    try:
        from db import is_guild_icon_taken
        if is_guild_icon_taken(icon):
            return False, "❌ Така іконка вже використовується іншою гільдією. Обери іншу іконку."
    except Exception:
        pass

    return True, icon
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_if_missing(root, target, marker, code):
    original = target.read_text(encoding="utf-8")
    if marker in original:
        return None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + code + "\n", encoding="utf-8")
    return backup, original, True


def patch_guild_system(root):
    target = root / "systems" / "guild_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/guild_system.py")
    backup, original, changed = append_if_missing(root, target, GUILD_SYSTEM_MARKER, GUILD_SYSTEM_APPEND)
    return target, backup, original, changed


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    backup, original, changed = append_if_missing(root, target, DB_MARKER, DB_APPEND)
    return target, backup, original, changed


def patch_guild_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, GUILD_HANDLER_MARKER, GUILD_HANDLER_APPEND)
    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_guild_system, patch_db, patch_guild_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        for file_path in changed_files:
            py_compile.compile(str(file_path), doraise=True)

        # Runtime DB migration / duplicate cleanup / unique index creation.
        sys.path.insert(0, str(root))
        from db import init_guild_system, ensure_unique_guild_icon_index, make_existing_guild_icons_unique
        init_guild_system()
        changes = make_existing_guild_icons_unique()
        ensure_unique_guild_icon_index()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_4a_unique_guild_icon.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.4a Unique Guild Icon застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in changed_files:
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо зроблено:")
    print("- іконка гільдії тепер має бути унікальна")
    print("- існуючі дублікати іконок автоматично розведено")
    print("- додано UNIQUE index: idx_guilds_icon_unique ON guilds(icon)")
    print("- при створенні гільдії зайнята іконка блокується")

    try:
        if changes:
            print("\nАвтоматично змінені дублікати іконок:")
            for guild_id, old_icon, new_icon, name, tag in changes:
                print(f"- guild_id={guild_id}: {old_icon} -> {new_icon} [{tag}] {name}")
        else:
            print("\nДублікатів іконок не знайдено або вони вже виправлені.")
    except Exception:
        pass

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
