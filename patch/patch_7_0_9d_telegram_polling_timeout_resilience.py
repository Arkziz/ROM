from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_9d_telegram_polling_timeout_resilience"
TARGET_RELATIVE_PATH = Path("main.py")
MARKER = "# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V1"

IMPORTS = '''
# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V1
import time
import requests
try:
    from telebot import apihelper
except Exception:
    apihelper = None
'''

HELPER_CODE = r'''

# ==============================
# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V1
# ==============================

# 7.0.9d
# Telegram іноді відповідає повільно на getUpdates і pyTelegramBotAPI кидає
# requests.exceptions.ReadTimeout. Це не ігрова помилка, а мережевий timeout.
# Цей wrapper не дає боту остаточно зупинитися після тимчасового таймауту.

if apihelper is not None:
    try:
        # Робимо read timeout трохи більшим, ніж стандартні 25 секунд.
        apihelper.READ_TIMEOUT = 60
        apihelper.CONNECT_TIMEOUT = 15
    except Exception:
        pass


def run_bot_polling_resilient(bot):
    while True:
        try:
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=45,
                skip_pending=True
            )
        except requests.exceptions.ReadTimeout as error:
            print(f"⚠️ Telegram polling read timeout, restarting polling in 5s: {error}")
            time.sleep(5)
        except requests.exceptions.ConnectionError as error:
            print(f"⚠️ Telegram polling connection error, restarting polling in 10s: {error}")
            time.sleep(10)
        except Exception as error:
            print(f"⚠️ Telegram polling unexpected error, restarting polling in 10s: {error}")
            time.sleep(10)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def find_infinity_polling_call(text):
    # Find the first bot.infinity_polling(...) call and return span including possible multiline parentheses.
    match = re.search(r"(?m)^(?P<indent>\s*)bot\.infinity_polling\s*\(", text)
    if not match:
        return None

    start = match.start()
    pos = match.end() - 1
    depth = 0
    in_str = None
    escape = False

    for i in range(pos, len(text)):
        ch = text[i]

        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_str:
                in_str = None
            continue

        if ch in ['"', "'"]:
            in_str = ch
            continue

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                # include rest of line
                line_end = text.find("\n", i)
                if line_end == -1:
                    line_end = len(text)
                else:
                    line_end += 1
                return start, line_end, match.group("indent")

    return None


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ TELEGRAM POLLING TIMEOUT RESILIENCE V1 уже застосований, пропускаю.")
        return

    call_info = find_infinity_polling_call(original)
    if not call_info:
        raise SystemExit(
            "❌ Не знайшов bot.infinity_polling(...) у main.py.\n"
            "Надішли main.py, і я дам точний патч."
        )

    backup_path = make_backup(root, target)

    start, end, indent = call_info
    replacement = f"{indent}run_bot_polling_resilient(bot)\n"

    text = original

    # Add imports after existing imports near top.
    insert_pos = 0
    import_matches = list(re.finditer(r"(?m)^(import\s+[^\n]+|from\s+[^\n]+\s+import\s+[^\n]+)\n", text))
    if import_matches:
        insert_pos = import_matches[-1].end()

    text = text[:insert_pos] + IMPORTS + text[insert_pos:]

    # Need recompute span after insertion if insertion before call.
    call_info = find_infinity_polling_call(text)
    start, end, indent = call_info
    replacement = f"{indent}run_bot_polling_resilient(bot)\n"
    text = text[:start] + replacement + text[end:]

    # Place helper before if __name__ if present, otherwise before polling replacement is already okay, but helper must exist before call.
    # Since polling call is usually at end after registrations, insert helper just before run_bot_polling_resilient(bot).
    run_pos = text.find("run_bot_polling_resilient(bot)")
    if run_pos == -1:
        target.write_text(original, encoding="utf-8")
        raise SystemExit("❌ Не вдалося вставити run_bot_polling_resilient(bot)")

    line_start = text.rfind("\n", 0, run_pos) + 1
    text = text[:line_start] + HELPER_CODE + "\n" + text[line_start:]

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9d_telegram_polling_timeout_resilience.\n"
            "main.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9d Telegram Polling Timeout Resilience застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ main.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- bot.infinity_polling(...) замінено на resilient wrapper")
    print("- ReadTimeout від api.telegram.org більше не має остаточно зупиняти бота")
    print("- після timeout polling перезапускається через 5 секунд")
    print("- збільшено read timeout Telegram API до 60 секунд")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\main.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
