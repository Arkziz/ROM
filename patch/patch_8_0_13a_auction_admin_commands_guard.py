from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_13a_auction_admin_commands_guard"
TARGET_RELATIVE = Path("handlers") / "auction_house.py"
MARKER = "# ✅ AUCTION ADMIN COMMAND GUARD V1"

APPEND_CODE = r'''

# ==============================
# ✅ AUCTION ADMIN COMMAND GUARD V1
# ==============================

# Захищає технічні команди Торгового Дому від звичайних гравців.
# Команди:
# /auction_sanity
# /auction_fix
# /auction_cleanup
# /auction_debug
#
# За замовчуванням дозволено user_id=243129101.
# Додатково можна задати змінну середовища:
# AUCTION_ADMIN_IDS=243129101,123456789
# або ADMIN_USER_IDS=243129101,123456789


def _auction_get_admin_ids_v1():
    import os

    raw = (
        os.getenv("AUCTION_ADMIN_IDS")
        or os.getenv("ADMIN_USER_IDS")
        or "243129101"
    )

    result = set()

    for part in str(raw).replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except Exception:
            pass

    return result


def _auction_is_admin_v1(user_id):
    return int(user_id) in _auction_get_admin_ids_v1()


def _auction_admin_denied_text_v1():
    return (
        "⛔ Команда доступна тільки адміністратору.\n\n"
        "Це технічна команда Торгового Дому."
    )


def _auction_safe_report_text_v1():
    try:
        from db import get_auction_diagnostics_report
        report = get_auction_diagnostics_report()
        return build_auction_diagnostics_text_v1(report)
    except Exception:
        try:
            from db import get_auction_cleanup_report
            result = get_auction_cleanup_report()
            return build_auction_cleanup_report_text_v2(result)
        except Exception as error:
            return f"❌ Не вдалося сформувати звіт Торгового Дому.\n\n{error}"


def _auction_register_admin_command_guard_v1(bot):

    @bot.message_handler(commands=["auction_sanity"])
    def auction_sanity_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        bot.send_message(message.chat.id, _auction_safe_report_text_v1())

    @bot.message_handler(commands=["auction_debug"])
    def auction_debug_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        bot.send_message(message.chat.id, _auction_safe_report_text_v1())

    @bot.message_handler(commands=["auction_fix"])
    def auction_fix_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        try:
            from db import run_auction_sanity_fix
            result = run_auction_sanity_fix()
            cleanup = result.get("cleanup", {})
            after = result.get("after", {})

            text = (
                "🛠 Auction sanity fix виконано.\n\n"
                f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
                f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
                f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
                f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
                f"{build_auction_diagnostics_text_v1(after)}"
            )

        except Exception as error:
            text = f"❌ Помилка auction_fix.\n\n{error}"

        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=["auction_cleanup"])
    def auction_cleanup_admin_guard_v1(message):
        if not _auction_is_admin_v1(message.from_user.id):
            bot.send_message(message.chat.id, _auction_admin_denied_text_v1())
            return

        try:
            from db import update_expired_auction_lots, get_auction_cleanup_report
            cleanup = update_expired_auction_lots()
            report = get_auction_cleanup_report()

            text = (
                "🧹 Cleanup виконано.\n\n"
                f"ACTIVE → EXPIRED_UNCLAIMED: {cleanup.get('expired_active', 0)}\n"
                f"EXPIRED_UNCLAIMED → DELETED: {cleanup.get('deleted_expired_unclaimed', 0)}\n"
                f"SOLD_UNCLAIMED → DELETED: {cleanup.get('deleted_sold_unclaimed', 0)}\n"
                f"Виправлено delete_after: {cleanup.get('fixed_missing_delete_after', 0)}\n\n"
                f"{build_auction_cleanup_report_text_v2(report)}"
            )

        except Exception as error:
            text = f"❌ Помилка auction_cleanup.\n\n{error}"

        bot.send_message(message.chat.id, text)


try:
    _auction_base_register_handlers_before_admin_guard_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_admin_guard_v1 = None


def register_auction_house_handlers(bot):
    # Реєструємо guard ПЕРЕД старими технічними handlers,
    # щоб звичайні гравці не могли виконати debug/fix/cleanup.
    _auction_register_admin_command_guard_v1(bot)

    if _auction_base_register_handlers_before_admin_guard_v1:
        _auction_base_register_handlers_before_admin_guard_v1(bot)
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
            "❌ Помилка компіляції після patch_8_0_13a_auction_admin_commands_guard.\n"
            "Файл handlers/auction_house.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.13a Auction admin command guard застосовано успішно.")
    print(f"✅ Backup: {backup}")
    print("✅ handlers/auction_house.py пройшов py_compile.")
    print("")
    print("Що змінено:")
    print("- /auction_sanity доступна тільки адміну")
    print("- /auction_debug доступна тільки адміну")
    print("- /auction_fix доступна тільки адміну")
    print("- /auction_cleanup доступна тільки адміну")
    print("- за замовчуванням admin user_id = 243129101")
    print("- можна задати AUCTION_ADMIN_IDS або ADMIN_USER_IDS")


if __name__ == "__main__":
    main()
