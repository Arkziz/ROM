from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "6_0_4a_refine_material_stack"
DB_MARKER = "# ✅ REFINE MATERIAL STACK FIX V1"

DB_APPEND_CODE = r'''

# ==============================
# ✅ REFINE MATERIAL STACK FIX V1
# ==============================

# 6.0.4a
# Камені/руни заточки мають стакатися великими пачками, а не по 20.
# ID:
# 401 — 🪨 Камінь Посилення
# 402 — 💎 Руна Успіху

REFINE_MATERIAL_MAX_STACK = 999


def ensure_refine_material_stack_sizes():
    """
    Гарантує, що матеріали заточки стакаються до 999.
    Безпечно викликати багато разів.
    """

    try:
        init_refine_system()
    except Exception:
        pass

    cursor.execute("""
    UPDATE items
    SET max_stack=?
    WHERE id IN (401, 402)
    """, (
        REFINE_MATERIAL_MAX_STACK,
    ))

    conn.commit()


def get_refine_material_stack_debug():
    """
    DEV/helper: повертає поточні max_stack для матеріалів заточки.
    """

    ensure_refine_material_stack_sizes()

    cursor.execute("""
    SELECT id, name, max_stack
    FROM items
    WHERE id IN (401, 402)
    ORDER BY id
    """)

    return cursor.fetchall()


# Автоматично фіксимо max_stack при імпорті db.py.
try:
    ensure_refine_material_stack_sizes()
except Exception:
    pass
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
        print("ℹ️ db.py: REFINE MATERIAL STACK FIX V1 уже застосований.")
    else:
        backup_path = make_backup(root, target)
        updated = original.rstrip() + "\n" + DB_APPEND_CODE + "\n"
        target.write_text(updated, encoding="utf-8")

        try:
            py_compile.compile(str(target), doraise=True)
        except Exception as error:
            target.write_text(original, encoding="utf-8")
            raise SystemExit(
                "❌ Помилка компіляції після patch_6_0_4a_refine_material_stack.\n"
                "db.py відновлено.\n\n"
                f"Помилка:\n{error}"
            )

        print("✅ Патч 6.0.4a stack fix застосовано успішно.")
        print(f"✅ Backup: {backup_path}")

    # Примусово виконуємо фікс у поточній БД без очікування перезапуску бота.
    import sys
    sys.path.insert(0, str(root))
    from db import ensure_refine_material_stack_sizes, get_refine_material_stack_debug

    ensure_refine_material_stack_sizes()
    print("✅ Поточна БД оновлена.")
    print("Матеріали заточки:")
    for row in get_refine_material_stack_debug():
        print("-", row)

    print("")
    print("Очікування:")
    print("- 401 🪨 Камінь Посилення max_stack = 999")
    print("- 402 💎 Руна Успіху max_stack = 999")


if __name__ == "__main__":
    main()
