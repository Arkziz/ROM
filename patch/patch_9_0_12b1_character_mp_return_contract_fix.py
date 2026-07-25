from pathlib import Path
from datetime import datetime
import py_compile


PATCH_NAME = "9_0_12b1_character_mp_return_contract_fix"
TARGET_RELATIVE_PATH = Path("systems") / "character_system.py"


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")

    backup_path = (
        backup_dir
        / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    )

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
            f"❌ Не знайдено файл: {target}"
        )

    original_text = target.read_text(encoding="utf-8")

    marker = (
        "# ✅ HOTFIX 9.0.12b1: "
        "CHARACTER MP RETURN CONTRACT FIX"
    )

    if marker in original_text:
        print("ℹ️ Патч уже застосовано. Пропускаю.")
        return

    backup_path = make_backup(root, target)

    patch_code = r'''

# ==============================
# ✅ HOTFIX 9.0.12b1: CHARACTER MP RETURN CONTRACT FIX
# ==============================

def get_user_mp(user_id):
    """
    Повертає MP у старому публічному форматі ROM.

    Важливо:
    handlers/profile.py та handlers/combat.py очікують словник:

        {
            "mp": current_mp,
            "max_mp": max_mp
        }

    Після refactor 9.0.12b функція помилково повертала int,
    через що виникало:

        AttributeError: 'int' object has no attribute 'get'
    """

    import db as _db

    try:
        user_id = int(user_id)
    except Exception:
        user_id = 0

    max_mp = int(get_max_mp(user_id) or 0)

    row = _db.conn.execute(
        """
        SELECT mp
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    ).fetchone()

    if not row:
        current_mp = max_mp
    else:
        try:
            current_mp = int(row[0] or 0)
        except Exception:
            current_mp = max_mp

    current_mp = max(0, min(current_mp, max_mp))

    return {
        "mp": current_mp,
        "max_mp": max_mp,
        "current_mp": current_mp
    }
'''

    new_text = original_text.rstrip() + "\n" + patch_code + "\n"

    target.write_text(new_text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)

    except Exception as error:
        target.write_text(original_text, encoding="utf-8")

        raise SystemExit(
            "❌ Помилка компіляції після патча.\n"
            "systems/character_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.12b1 застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ systems/character_system.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- get_user_mp() знову повертає словник")
    print("- профіль може читати mp_data.get('mp')")
    print("- combat може читати mp_data.get('mp')")
    print("- max_mp повертається разом із поточним MP")


if __name__ == "__main__":
    main()