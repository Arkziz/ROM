from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "6_0_6a_combat_rate_limit_safe_send"
TARGET_RELATIVE_PATH = Path("handlers") / "combat.py"
MARKER = "# ✅ COMBAT SAFE SEND RATE LIMIT V1"

APPEND_CODE = r'''

# ==============================
# ✅ COMBAT SAFE SEND RATE LIMIT V1
# ==============================

# Telegram може повернути 429 Too Many Requests, якщо бот надсилає багато повідомлень
# або якщо старі callback-и обробляються повторно після exception.
# Цей wrapper не дає polling падати через 429: чекає retry_after і повторює send один раз.


def patch_combat_bot_rate_limit_safe_send(bot):
    if getattr(bot, "_rom_safe_send_patched", False):
        return

    original_send_message = bot.send_message
    bot._rom_original_send_message = original_send_message

    def safe_send_message(chat_id, text, *args, **kwargs):
        try:
            return original_send_message(chat_id, text, *args, **kwargs)
        except Exception as error:
            retry_after = None
            error_code = getattr(error, "error_code", None)
            result_json = getattr(error, "result_json", None)

            if isinstance(result_json, dict):
                parameters = result_json.get("parameters", {}) or {}
                retry_after = parameters.get("retry_after")

                if error_code is None:
                    error_code = result_json.get("error_code")

            description = str(error)

            is_rate_limit = (
                error_code == 429
                or "Too Many Requests" in description
                or "retry after" in description
            )

            if not is_rate_limit:
                raise

            if retry_after is None:
                retry_after = 3

            try:
                retry_after = int(retry_after)
            except Exception:
                retry_after = 3

            retry_after = max(1, min(60, retry_after))

            try:
                import time
                print(f"⚠️ Telegram rate limit 429. Waiting {retry_after + 1}s before retry send_message.")
                time.sleep(retry_after + 1)
                return original_send_message(chat_id, text, *args, **kwargs)
            except Exception as retry_error:
                print(f"❌ send_message retry failed after 429: {retry_error}")
                return None

    bot.send_message = safe_send_message
    bot._rom_safe_send_patched = True
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"

    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def insert_register_call(text):
    if "patch_combat_bot_rate_limit_safe_send(bot)" in text:
        return text, False

    pattern = re.compile(r"def\s+register_combat_handlers\s*\(\s*bot\s*\)\s*:\n")
    match = pattern.search(text)

    if not match:
        raise SystemExit("❌ Не знайдено def register_combat_handlers(bot) у handlers/combat.py")

    insert_pos = match.end()
    call = (
        "    # 6.0.6a: захист від Telegram 429 Too Many Requests у бойових повідомленнях\n"
        "    patch_combat_bot_rate_limit_safe_send(bot)\n"
    )

    text = text[:insert_pos] + call + text[insert_pos:]
    return text, True


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Запускай патч із ROM або з ROM\\patch."
        )

    original = target.read_text(encoding="utf-8")
    backup_path = make_backup(root, target)

    text = original
    changed = False

    if MARKER not in text:
        text = text.rstrip() + "\n" + APPEND_CODE + "\n"
        changed = True
        print("✅ combat.py: додано safe send wrapper від 429.")
    else:
        print("ℹ️ combat.py: safe send wrapper вже є.")

    text, call_changed = insert_register_call(text)
    changed = changed or call_changed

    if not changed:
        print("ℹ️ combat.py: змін не потрібно.")
        return

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_6_0_6a_combat_rate_limit_safe_send.\n"
            "handlers/combat.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 6.0.6a застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/combat.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- combat send_message більше не валить polling при Telegram 429")
    print("- при 429 бот чекає retry_after і повторює надсилання один раз")
    print("- це має прибрати зависання/падіння після швидких натискань бойових inline-кнопок")
    print("")
    print("Після патча обовʼязково перезапусти бота.")


if __name__ == "__main__":
    main()
