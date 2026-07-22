from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_9d2_telegram_polling_timeout_resilience_fix"
TARGET_RELATIVE_PATH = Path("main.py")
MARKER = "# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V2"

IMPORTS = '''
# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V2
import time
import requests
try:
    from telebot import apihelper
except Exception:
    apihelper = None
'''

HELPER_CODE = r'''

# ==============================
# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V2
# ==============================

# 7.0.9d2
# Telegram іноді дає ReadTimeout на getUpdates.
# Це мережевий timeout, не помилка логіки гри.
# Wrapper нижче перезапускає polling після тимчасових мережевих помилок.

if apihelper is not None:
    try:
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
    match = re.search(r"(?m)^(?P<indent>\s*)bot\.infinity_polling\s*\(", text)
    if not match:
        return None

    start = match.start()
    pos = match.end() - 1
    depth = 0
    in_str = None
    triple = False
    escape = False

    i = pos
    while i < len(text):
        ch = text[i]

        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif triple and text.startswith(in_str * 3, i):
                in_str = None
                triple = False
                i += 2
            elif not triple and ch == in_str:
                in_str = None
            i += 1
            continue

        if text.startswith('"""', i) or text.startswith("'''", i):
            in_str = text[i]
            triple = True
            i += 3
            continue

        if ch in ['"', "'"]:
            in_str = ch
            triple = False
            i += 1
            continue

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                line_end = text.find("\n", i)
                if line_end == -1:
                    line_end = len(text)
                else:
                    line_end += 1
                return start, line_end, match.group("indent")

        i += 1

    return None


def insert_after_top_imports(text, insert_text):
    lines = text.splitlines(True)
    pos = 0
    in_import_block = True

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            pos = idx + 1
            continue

        if stripped.startswith("import ") or stripped.startswith("from "):
            pos = idx + 1
            continue

        break

    return "".join(lines[:pos]) + insert_text + "".join(lines[pos:])


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ TELEGRAM POLLING TIMEOUT RESILIENCE V2 уже застосований, пропускаю.")
        return

    if "bot.infinity_polling" not in original:
        raise SystemExit("❌ У main.py не знайдено bot.infinity_polling(...)")

    backup_path = make_backup(root, target)
    text = original

    # 1) Add imports near top, not inside try blocks.
    text = insert_after_top_imports(text, IMPORTS)

    # 2) Add helper before the polling call, but before any surrounding try block if possible.
    call_info = find_infinity_polling_call(text)
    if not call_info:
        target.write_text(original, encoding="utf-8")
        raise SystemExit("❌ Не вдалося знайти повний bot.infinity_polling(...) після вставки imports")

    call_start, call_end, indent = call_info

    # Find nearest previous top/indented line that is exactly try: with same indent as polling minus 4 spaces.
    helper_insert_pos = call_start
    current_indent = indent
    parent_indent = current_indent[:-4] if len(current_indent) >= 4 else ""
    before_call = text[:call_start]
    lines = before_call.splitlines(True)
    char_pos = 0
    try_line_start = None
    for line in lines:
        line_start = char_pos
        char_pos += len(line)
        if line == f"{parent_indent}try:\n" or line.rstrip("\n") == f"{parent_indent}try:":
            try_line_start = line_start

    if try_line_start is not None:
        helper_insert_pos = try_line_start

    text = text[:helper_insert_pos] + HELPER_CODE + "\n" + text[helper_insert_pos:]

    # 3) Replace the polling call after helper insertion. Re-find call.
    call_info = find_infinity_polling_call(text)
    if not call_info:
        target.write_text(original, encoding="utf-8")
        raise SystemExit("❌ Не вдалося повторно знайти bot.infinity_polling(...) після вставки helper")

    call_start, call_end, indent = call_info
    text = text[:call_start] + f"{indent}run_bot_polling_resilient(bot)\n" + text[call_end:]

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9d2_telegram_polling_timeout_resilience_fix.\n"
            "main.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9d2 Telegram Polling Timeout Resilience Fix застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ main.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- виправлено проблему indentation з попереднього 7.0.9d")
    print("- bot.infinity_polling(...) замінено на run_bot_polling_resilient(bot)")
    print("- ReadTimeout від api.telegram.org більше не має остаточно зупиняти бота")
    print("- після timeout polling перезапускається через 5 секунд")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\main.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
