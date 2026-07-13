from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(".")
FILES = [
    Path("db.py"),
    Path("handlers/start.py"),
    Path("handlers/profile.py"),
    Path("handlers/city.py"),
]


def backup_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Не знайдено файл: {path}")

    backup_path = path.with_suffix(path.suffix + ".bak_passive_regen")

    if not backup_path.exists():
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[OK] backup: {backup_path}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")
    print(f"[OK] updated: {path}")


def add_to_db_import(text: str, name: str) -> str:
    """
    Додає name у перший from db import (...) блок.
    """
    if name in text:
        return text

    marker = "from db import ("
    start = text.find(marker)

    if start == -1:
        raise RuntimeError("Не знайдено from db import (...)")

    end = text.find(")", start)

    if end == -1:
        raise RuntimeError("Не знайдено кінець from db import (...)")

    before = text[:end]
    after = text[end:]

    if before.rstrip().endswith(","):
        before += f"\n    {name},"
    else:
        before += f",\n    {name},"

    return before + after


def insert_after_once(text: str, anchor: str, insertion: str) -> str:
    if insertion.strip() in text:
        return text

    idx = text.find(anchor)

    if idx == -1:
        raise RuntimeError(f"Не знайдено anchor:\n{anchor}")

    insert_pos = idx + len(anchor)

    return text[:insert_pos] + insertion + text[insert_pos:]


def insert_after_def_line(text: str, def_name: str, line_to_insert: str) -> str:
    """
    Додає рядок одразу після def ...:
    """
    if line_to_insert.strip() in text:
        return text

    marker = f"def {def_name}("
    start = text.find(marker)

    if start == -1:
        raise RuntimeError(f"Не знайдено функцію {def_name}")

    line_end = text.find("\n", start)

    if line_end == -1:
        raise RuntimeError(f"Не знайдено кінець рядка def {def_name}")

    return text[:line_end + 1] + line_to_insert + text[line_end + 1:]


def patch_db():
    path = Path("db.py")
    backup_file(path)
    text = read(path)

    # Прибираємо стару помилку, якщо вона десь знову залишилась.
    text = text.replace("if not row or not rowreturn {", "if not row or not row")
    text = text.replace("rowreturn", "row[0]")

    if "def process_passive_regeneration(user_id):" not in text:
        block = r'''

# ==============================
# ✅ PASSIVE HP / MP REGEN SYSTEM
# ==============================

from datetime import datetime


def init_passive_regen_system():
    try:
        cursor.execute("""
        ALTER TABLE users
        ADD COLUMN last_regen_at TEXT DEFAULT ''
        """)
    except Exception:
        pass

    conn.commit()


def update_last_regen_timestamp(user_id):
    init_passive_regen_system()

    cursor.execute("""
    UPDATE users
    SET last_regen_at=?
    WHERE user_id=?
    """, (
        datetime.utcnow().isoformat(),
        user_id
    ))

    conn.commit()


# ==============================
# ✅ OVERRIDE refresh_user_mp
# ==============================

def refresh_user_mp(user_id):
    """
    Оновлює max_mp для mana-класів, але НЕ відновлює MP автоматично до максимуму.

    Логіка:
    - якщо персонаж вперше став mana-класом, MP = max_mp;
    - якщо MP вже витрачалась, поточна MP зберігається;
    - якщо max_mp змінився через екіпірування, поточна MP обрізається до нового максимуму.
    """

    init_character_class_system()

    class_key = get_character_class(user_id)
    resource_type = CLASS_CONFIGS.get(class_key, {}).get("resource", "")

    if resource_type != "mana":
        cursor.execute("""
        UPDATE users
        SET mp=0,
            max_mp=0
        WHERE user_id=?
        """, (user_id,))

        conn.commit()

        return {
            "mp": 0,
            "max_mp": 0
        }

    new_max_mp = get_max_mp(user_id)

    cursor.execute("""
    SELECT mp, max_mp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "mp": 0,
            "max_mp": 0
        }

    current_mp, old_max_mp = row

    current_mp = current_mp or 0
    old_max_mp = old_max_mp or 0

    if old_max_mp <= 0 and current_mp <= 0:
        current_mp = new_max_mp

    if current_mp > new_max_mp:
        current_mp = new_max_mp

    if current_mp < 0:
        current_mp = 0

    cursor.execute("""
    UPDATE users
    SET mp=?,
        max_mp=?
    WHERE user_id=?
    """, (
        current_mp,
        new_max_mp,
        user_id
    ))

    conn.commit()

    return {
        "mp": current_mp,
        "max_mp": new_max_mp
    }


# ==============================
# ✅ OVERRIDE get_user_mp
# ==============================

def get_user_mp(user_id):
    refresh_user_mp(user_id)

    cursor.execute("""
    SELECT mp, max_mp
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "mp": 0,
            "max_mp": 0
        }

    mp, max_mp = row

    return {
        "mp": mp or 0,
        "max_mp": max_mp or 0
    }


def process_passive_regeneration(user_id):
    """
    Пасивне відновлення поза боєм.

    За кожну повну хвилину:
    - +5% від max HP
    - +5% від max MP, якщо клас використовує ману

    Викликається під час взаємодії з ботом:
    /start, профіль, місто, роззирнутися тощо.
    """

    init_passive_regen_system()
    init_character_class_system()

    cursor.execute("""
    SELECT last_regen_at
    FROM users
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "success": False,
            "message": "❌ Персонажа не знайдено."
        }

    last_regen_at = row[0]
    now = datetime.utcnow()

    if not last_regen_at:
        update_last_regen_timestamp(user_id)

        return {
            "success": True,
            "minutes": 0,
            "hp_restored": 0,
            "mp_restored": 0
        }

    try:
        previous = datetime.fromisoformat(last_regen_at)
    except Exception:
        update_last_regen_timestamp(user_id)

        return {
            "success": True,
            "minutes": 0,
            "hp_restored": 0,
            "mp_restored": 0
        }

    elapsed_seconds = int((now - previous).total_seconds())

    if elapsed_seconds < 60:
        return {
            "success": True,
            "minutes": 0,
            "hp_restored": 0,
            "mp_restored": 0
        }

    minutes = elapsed_seconds // 60

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    hp_regen_per_minute = max(
        1,
        int(round(max_hp * 0.05))
    )

    new_hp = min(
        max_hp,
        current_hp + (hp_regen_per_minute * minutes)
    )

    hp_restored = max(0, new_hp - current_hp)

    set_current_hp(user_id, new_hp)

    mp_restored = 0

    profile_summary = get_character_profile_summary(user_id)

    if profile_summary.get("resource_type") == "mana":
        mp_data = get_user_mp(user_id)

        current_mp = mp_data.get("mp", 0)
        max_mp = mp_data.get("max_mp", 0)

        if max_mp > 0:
            mp_regen_per_minute = max(
                1,
                int(round(max_mp * 0.05))
            )

            new_mp = min(
                max_mp,
                current_mp + (mp_regen_per_minute * minutes)
            )

            mp_restored = max(0, new_mp - current_mp)

            cursor.execute("""
            UPDATE users
            SET mp=?
            WHERE user_id=?
            """, (
                new_mp,
                user_id
            ))

    cursor.execute("""
    UPDATE users
    SET last_regen_at=?
    WHERE user_id=?
    """, (
        now.isoformat(),
        user_id
    ))

    conn.commit()

    return {
        "success": True,
        "minutes": minutes,
        "hp_restored": hp_restored,
        "mp_restored": mp_restored
    }
'''
        text += block

    write(path, text)


def patch_start():
    path = Path("handlers/start.py")
    backup_file(path)
    text = read(path)

    text = add_to_db_import(text, "process_passive_regeneration")

    anchor = "    create_user(user_id)"
    insertion = "\n    process_passive_regeneration(user_id)"

    if insertion.strip() not in text:
        text = insert_after_once(text, anchor, insertion)

    write(path, text)


def patch_profile():
    path = Path("handlers/profile.py")
    backup_file(path)
    text = read(path)

    text = add_to_db_import(text, "process_passive_regeneration")

    text = insert_after_def_line(
        text,
        "build_character_text",
        "    process_passive_regeneration(user_id)\n"
    )

    text = insert_after_def_line(
        text,
        "build_stats_text",
        "    process_passive_regeneration(user_id)\n"
    )

    text = insert_after_def_line(
        text,
        "build_equipment_text",
        "    process_passive_regeneration(user_id)\n"
    )

    write(path, text)


def patch_city():
    path = Path("handlers/city.py")
    backup_file(path)
    text = read(path)

    text = add_to_db_import(text, "process_passive_regeneration")

    text = insert_after_def_line(
        text,
        "build_main_menu_text",
        "    process_passive_regeneration(user_id)\n"
    )

    text = insert_after_def_line(
        text,
        "build_city_text",
        "    process_passive_regeneration(user_id)\n"
    )

    write(path, text)


def main():
    print("== Passive regen patch ==")

    for file_path in FILES:
        if not file_path.exists():
            raise FileNotFoundError(f"Не знайдено: {file_path}")

    patch_db()
    patch_start()
    patch_profile()
    patch_city()

    print("\n✅ Готово.")
    print("Тепер перевір синтаксис:")
    print("python -m py_compile db.py handlers/start.py handlers/profile.py handlers/city.py")


if __name__ == "__main__":
    main()