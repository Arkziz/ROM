from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_9d3_telegram_polling_timeout_resilience_safe"
TARGET_RELATIVE_PATH = Path("main.py")
MARKER = "# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V3"

TOP_CODE = r'''
# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V3
import time as _rom_polling_time

try:
    import requests as _rom_polling_requests
except Exception:
    _rom_polling_requests = None

try:
    from telebot import apihelper as _rom_polling_apihelper
except Exception:
    _rom_polling_apihelper = None

if _rom_polling_apihelper is not None:
    try:
        _rom_polling_apihelper.READ_TIMEOUT = 60
        _rom_polling_apihelper.CONNECT_TIMEOUT = 15
    except Exception:
        pass


def run_bot_polling_resilient(bot):
    """
    Keeps Telegram polling alive after temporary network timeouts.
    """
    while True:
        try:
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=45,
                skip_pending=True
            )
        except Exception as error:
            error_name = type(error).__name__
            error_text = str(error)

            is_timeout = False
            is_connection = False

            if _rom_polling_requests is not None:
                try:
                    is_timeout = isinstance(error, _rom_polling_requests.exceptions.ReadTimeout)
                    is_connection = isinstance(error, _rom_polling_requests.exceptions.ConnectionError)
                except Exception:
                    pass

            if is_timeout or "Read timed out" in error_text or "ReadTimeout" in error_name:
                print(f"⚠️ Telegram polling read timeout, restarting polling in 5s: {error}")
                _rom_polling_time.sleep(5)
                continue

            if is_connection or "Connection" in error_name or "connection" in error_text.lower():
                print(f"⚠️ Telegram polling connection error, restarting polling in 10s: {error}")
                _rom_polling_time.sleep(10)
                continue

            print(f"⚠️ Telegram polling unexpected error, restarting polling in 10s: {error}")
            _rom_polling_time.sleep(10)
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


def find_safe_top_insert_pos(text):
    """
    Insert after shebang, encoding comment, module docstring, and __future__ imports.
    Avoids inserting inside any import(... ) block.
    """
    pos = 0

    # shebang
    if text.startswith("#!"):
        nl = text.find("\n", pos)
        pos = len(text) if nl == -1 else nl + 1

    # encoding comment in first/second line
    encoding_pattern = re.compile(r"#.*coding[:=]\s*[-\w.]+")
    for _ in range(2):
        line_end = text.find("\n", pos)
        if line_end == -1:
            line_end = len(text)
        line = text[pos:line_end]
        if encoding_pattern.search(line):
            pos = line_end + (1 if line_end < len(text) else 0)
        else:
            break

    # skip blank/comment lines after shebang/encoding
    while True:
        line_end = text.find("\n", pos)
        if line_end == -1:
            line_end = len(text)
        line = text[pos:line_end]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            pos = line_end + (1 if line_end < len(text) else 0)
            continue
        break

    # module docstring with triple quotes
    remaining = text[pos:]
    if remaining.startswith('"""') or remaining.startswith("'''"):
        quote = remaining[:3]
        end = text.find(quote, pos + 3)
        if end != -1:
            end += 3
            nl = text.find("\n", end)
            pos = len(text) if nl == -1 else nl + 1

    # __future__ imports must remain before normal imports/code
    while True:
        line_end = text.find("\n", pos)
        if line_end == -1:
            line_end = len(text)
        line = text[pos:line_end]
        if line.strip().startswith("from __future__ import "):
            pos = line_end + (1 if line_end < len(text) else 0)
            continue
        break

    return pos


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ TELEGRAM POLLING TIMEOUT RESILIENCE V3 уже застосований, пропускаю.")
        return

    call_info = find_infinity_polling_call(original)
    if not call_info:
        raise SystemExit(
            "❌ Не знайшов bot.infinity_polling(...) у main.py.\n"
            "main.py не змінено."
        )

    backup_path = make_backup(root, target)

    insert_pos = find_safe_top_insert_pos(original)
    text = original[:insert_pos] + TOP_CODE + "\n" + original[insert_pos:]

    call_info = find_infinity_polling_call(text)
    if not call_info:
        target.write_text(original, encoding="utf-8")
        raise SystemExit("❌ Не вдалося повторно знайти bot.infinity_polling(...) після вставки helper")

    start, end, indent = call_info
    text = text[:start] + f"{indent}run_bot_polling_resilient(bot)\n" + text[end:]

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_9d3_telegram_polling_timeout_resilience_safe.\n"
            "main.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.9d3 Telegram Polling Timeout Resilience Safe застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ main.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- helper вставляється у безпечне місце на початку файлу")
    print("- bot.infinity_polling(...) замінено на run_bot_polling_resilient(bot)")
    print("- Telegram ReadTimeout більше не має зупиняти бота остаточно")
    print("- після timeout polling перезапускається через 5 секунд")
    print("")
    print("Після патча:")
    print("python -m py_compile .\\main.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
