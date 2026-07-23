from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "9_0_2a_player_add_kill_signature_fix"
TARGET_RELATIVE = Path("systems") / "player_system.py"
MARKER = "# ✅ ROM 9.0.2a PLAYER ADD_KILL SIGNATURE FIX V1"

APPEND_CODE = r'''

# ==============================
# ✅ ROM 9.0.2a PLAYER ADD_KILL SIGNATURE FIX V1
# ==============================

try:
    _player_system_base_add_kill_before_signature_fix_v1 = add_kill
except NameError:
    _player_system_base_add_kill_before_signature_fix_v1 = None


def add_kill(user_id: int, amount: int = 1):
    """
    Compatibility fix.

    У старому db.py актуальна legacy-функція add_kill() має сигнатуру:
        add_kill(user_id)

    А facade 9.0.2 викликав legacy як:
        legacy(user_id, amount)

    Через це після бою виникало:
        TypeError: add_kill() takes 1 positional argument but 2 were given

    Правильна сумісна логіка:
    - якщо amount == 1, пробуємо старий legacy(user_id);
    - якщо amount > 1 і legacy підтримує тільки 1 аргумент, викликаємо legacy(user_id) кілька разів;
    - якщо legacy відсутній, використовуємо fallback UPDATE.
    """

    legacy = _legacy_function("add_kill")

    if legacy:
        try:
            return legacy(user_id, amount)
        except TypeError:
            safe_amount = max(1, int(amount or 1))
            result = None
            for _ in range(safe_amount):
                result = legacy(user_id)
            return result

    try:
        safe_amount = max(1, int(amount or 1))
        _execute_commit(
            "UPDATE users SET kills=COALESCE(kills, 0)+? WHERE user_id=?",
            (safe_amount, user_id),
        )
        return True
    except Exception:
        return False
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
    target = root / TARGET_RELATIVE

    if not target.exists():
        raise SystemExit(f"❌ Не знайдено файл: {target}")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ Патч уже застосовано раніше.")
        return

    backup = make_backup(root, target)

    try:
        target.write_text(original.rstrip() + "\n" + APPEND_CODE + "\n", encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_9_0_2a_player_add_kill_signature_fix.\n"
            "Файл systems/player_system.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 9.0.2a Player add_kill signature fix застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ systems/player_system.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- add_kill(user_id, amount=1) тепер сумісний зі старим legacy add_kill(user_id)")
    print("- перемога в бою більше не має падати з TypeError")
    print("- якщо amount > 1, старий legacy викликається кілька разів")


if __name__ == "__main__":
    main()
