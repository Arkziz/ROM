from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_9c_contract_target_kills_5"
TARGET_RELATIVE_PATH = Path("db.py")
MARKER = "# ✅ CONTRACT TARGET KILLS 5 V1"

APPEND_CODE = r'''

# ==============================
# ✅ CONTRACT TARGET KILLS 5 V1
# ==============================

# 7.0.9c
# Баланс контрактів:
# було: 10 вбивств
# стало: 5 вбивств
#
# Важливо:
# - нові контракти створюються з target_kills=5;
# - старі активні контракти з target_kills > 5 автоматично стискаються до 5;
# - якщо у старому активному контракті вже current_kills >= 5, контракт стає completed.

CONTRACT_TARGET_KILLS = 5


def migrate_active_contracts_target_kills_to_5():
    init_contract_system()

    cursor.execute("""
    UPDATE user_active_contracts
    SET target_kills=5
    WHERE target_kills > 5
    """)

    cursor.execute("""
    UPDATE user_active_contracts
    SET completed=1,
        current_kills=5
    WHERE target_kills=5
      AND current_kills >= 5
      AND reward_claimed=0
    """)

    conn.commit()

    return True


try:
    migrate_active_contracts_target_kills_to_5()
except Exception as _contract_target_kills_5_error:
    print(f"⚠️ Contract target kills migration failed: {_contract_target_kills_5_error}")
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def replace_existing_constants(text):
    # First, normalize direct assignments in the current file so readable source also shows 5.
    text = text.replace("CONTRACT_TARGET_KILLS = 10", "CONTRACT_TARGET_KILLS = 5")
    return text


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ CONTRACT TARGET KILLS 5 V1 уже застосований, пропускаю.")
        return

    if "CONTRACT_TARGET_KILLS" not in original:
        raise SystemExit("❌ У db.py не знайдено CONTRACT_TARGET_KILLS")

    backup_path = make_backup(root, target)

    updated = replace_existing_constants(original).rstrip() + "\n" + APPEND_CODE + "\n"
    target.write_text(updated, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9c_contract_target_kills_5.\n"
            "db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    try:
        sys.path.insert(0, str(root))
        from db import migrate_active_contracts_target_kills_to_5
        migrate_active_contracts_target_kills_to_5()
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка міграції активних контрактів після patch_7_0_9c_contract_target_kills_5.\n"
            "db.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9c Contract Target Kills 5 застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ db.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- нові контракти тепер потребують 5 вбивств замість 10")
    print("- активні контракти з target_kills > 5 зменшені до 5")
    print("- якщо активний контракт уже мав 5+ вбивств, він позначений як виконаний")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\db.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
