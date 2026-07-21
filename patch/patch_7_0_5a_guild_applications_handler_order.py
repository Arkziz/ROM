from pathlib import Path
from datetime import datetime
import py_compile
import re

PATCH_NAME = "7_0_5a_guild_applications_handler_order"
TARGET_RELATIVE_PATH = Path("handlers") / "guild.py"
MARKER = "# ✅ GUILD APPLICATIONS HANDLER ORDER FIX V1"


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
    target = root / TARGET_RELATIVE_PATH

    if not target.exists():
        raise SystemExit(
            f"❌ Не знайдено файл: {target}\n"
            "Спочатку застосуй 7.0.5 для handlers/guild.py."
        )

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print("ℹ️ GUILD APPLICATIONS HANDLER ORDER FIX V1 уже застосований, пропускаю.")
        return

    backup_path = make_backup(root, target)
    text = original

    # У старому register_guild_handlers() вже є handler для кнопки 📧/📨 Заявки,
    # який показує placeholder. Він реєструється раніше, ніж wrapper з 7.0.5,
    # тому перехоплює кнопку першим. Міняємо його тіло на реальний show_guild_applications().
    old_block = '''    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message(message):
        send_guild_section(bot, message, build_guild_placeholder_text("📨 Заявки до гільдії", "7.0.5"))
'''

    new_block = '''    @bot.message_handler(func=lambda message: message.text == "📨 Заявки")
    def guild_applications_message(message):
        show_guild_applications(bot, message)
        # ✅ GUILD APPLICATIONS HANDLER ORDER FIX V1
'''

    if old_block in text:
        text = text.replace(old_block, new_block, 1)
    else:
        # Fallback regex for formatting variations.
        pattern = re.compile(
            r'    @bot\.message_handler\(func=lambda message: message\.text == "📨 Заявки"\)\n'
            r'    def guild_applications_message\(message\):\n'
            r'        send_guild_section\(bot, message, build_guild_placeholder_text\("📨 Заявки до гільдії", "7\.0\.5"\)\)\n',
            flags=re.M,
        )
        text, count = pattern.subn(new_block, text, count=1)
        if count == 0:
            target.write_text(original, encoding="utf-8")
            raise SystemExit(
                "❌ Не знайшов старий placeholder-handler для 📨 Заявки.\n"
                "Надішли актуальний handlers/guild.py, і я дам точний патч."
            )

    target.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as error:
        target.write_text(original, encoding="utf-8")
        raise SystemExit(
            "❌ Помилка компіляції після patch_7_0_5a_guild_applications_handler_order.\n"
            "handlers/guild.py відновлено.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.5a Guild Applications Handler Order Fix застосовано успішно.")
    print(f"✅ Backup: {backup_path}")
    print("✅ handlers/guild.py пройшов py_compile.")
    print("")
    print("Що виправлено:")
    print("- стара кнопка 📨 Заявки більше не показує placeholder 7.0.5")
    print("- тепер вона відкриває реальний список pending-заявок")
    print("- причина була в порядку реєстрації handlers: старий handler спрацьовував раніше нового")
    print("")
    print("Після патча перезапусти бота.")


if __name__ == "__main__":
    main()
