from pathlib import Path
from datetime import datetime
import py_compile
import re
import sys

PATCH_NAME = "8_0_2_auction_house_ui"
HANDLER_PATH = Path("handlers") / "auction_house.py"

AUCTION_HANDLER_CODE = r'''
from telebot import types

from db import (
    init_auction_house,
    get_auction_house_stats,
    update_expired_auction_lots,
)

try:
    from keyboards import city_kb
except Exception:
    city_kb = None

try:
    from keyboards import main_kb
except Exception:
    main_kb = None


AUCTION_MENU_BUTTON = "🏛️ Торговий дім"
AUCTION_BUY_BUTTON = "🛒 Купити"
AUCTION_SELL_BUTTON = "➕ Виставити товар"
AUCTION_MY_LOTS_BUTTON = "📦 Мої лоти"
AUCTION_UNCLAIMED_ITEMS_BUTTON = "📬 Незабрані предмети"
AUCTION_SOLD_BUTTON = "💰 Завершені продажі"
AUCTION_HISTORY_BUTTON = "📜 Історія"
AUCTION_BACK_TO_CITY_BUTTON = "🔙 Місто"


# ==============================
# KEYBOARDS
# ==============================

def auction_house_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(AUCTION_BUY_BUTTON, AUCTION_SELL_BUTTON)
    kb.add(AUCTION_MY_LOTS_BUTTON)
    kb.add(AUCTION_UNCLAIMED_ITEMS_BUTTON, AUCTION_SOLD_BUTTON)
    kb.add(AUCTION_HISTORY_BUTTON)
    kb.add(AUCTION_BACK_TO_CITY_BUTTON)
    return kb


def get_city_reply_keyboard():
    if city_kb:
        try:
            return city_kb()
        except Exception:
            pass

    if main_kb:
        try:
            return main_kb()
        except Exception:
            pass

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🏙️ Місто")
    return kb


# ==============================
# TEXT BUILDERS
# ==============================

def build_auction_house_text(user_id):
    init_auction_house()
    cleanup = update_expired_auction_lots()
    stats = get_auction_house_stats()

    active = int(stats.get("ACTIVE", 0) or 0)
    sold_unclaimed = int(stats.get("SOLD_UNCLAIMED", 0) or 0)
    expired_unclaimed = int(stats.get("EXPIRED_UNCLAIMED", 0) or 0)

    text = (
        "🏛️ Торговий дім\n\n"
        "Тут гравці можуть виставляти товари на продаж, купувати предмети інших героїв "
        "і поступово формувати ринкову економіку світу.\n\n"
        "Доступні дії:\n"
        "• 🛒 Купити — перегляд активних лотів.\n"
        "• ➕ Виставити товар — продати предмет іншому гравцю.\n"
        "• 📦 Мої лоти — твої активні продажі.\n"
        "• 📬 Незабрані предмети — лоти, термін яких завершився.\n"
        "• 💰 Завершені продажі — забрати золото за продані товари.\n"
        "• 📜 Історія — історія операцій.\n\n"
        "ℹ️ Правила:\n"
        "• Активний лот існує 7 днів.\n"
        "• Незабрані предмети та золото зберігаються 30 днів.\n"
        "• Максимум активних лотів: 20.\n"
        "• Мінімальна ціна: 1.0 золота.\n"
        "• Максимальна ціна: 999999.0 золота.\n\n"
        "📊 Поточний стан ринку:\n"
        f"• Активні лоти: {active}\n"
        f"• Продані, золото не забране: {sold_unclaimed}\n"
        f"• Завершені, предмети не забрані: {expired_unclaimed}\n"
    )

    if cleanup.get("expired") or cleanup.get("deleted"):
        text += (
            "\n🧹 Оновлення ринку:\n"
            f"• Завершено лотів: {cleanup.get('expired', 0)}\n"
            f"• Видалено прострочених записів: {cleanup.get('deleted', 0)}\n"
        )

    return text


def build_auction_placeholder_text(title, description):
    return (
        f"{title}\n\n"
        f"{description}\n\n"
        "Цей розділ буде реалізовано в наступних етапах Торгового Дому 8.0.\n\n"
        "Поточний етап 8.0.2 додав головне меню та підключив ядро БД."
    )


# ==============================
# HANDLER REGISTRATION
# ==============================

def register_auction_house_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_MENU_BUTTON)
    def show_auction_house(message):
        user_id = message.from_user.id
        bot.send_message(
            message.chat.id,
            build_auction_house_text(user_id),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_BACK_TO_CITY_BUTTON)
    def auction_back_to_city(message):
        bot.send_message(
            message.chat.id,
            "🏙️ Ти повернувся до міста.",
            reply_markup=get_city_reply_keyboard()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_BUY_BUTTON)
    def auction_buy_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "🛒 Купити",
                "Тут буде перегляд активних лотів, фільтри, сортування та пошук."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
    def auction_sell_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "➕ Виставити товар",
                "Тут буде вибір категорії, предмета, кількості для стеків, ціни та підтвердження лота."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_MY_LOTS_BUTTON)
    def auction_my_lots_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📦 Мої лоти",
                "Тут будуть активні лоти гравця, пагінація і зняття з продажу."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_UNCLAIMED_ITEMS_BUTTON)
    def auction_unclaimed_items_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📬 Незабрані предмети",
                "Тут будуть предмети з лотів, термін яких завершився, але які ще можна забрати."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_SOLD_BUTTON)
    def auction_sold_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "💰 Завершені продажі",
                "Тут буде золото за продані лоти, яке продавець має забрати вручну."
            ),
            reply_markup=auction_house_kb()
        )

    @bot.message_handler(func=lambda m: m.text == AUCTION_HISTORY_BUTTON)
    def auction_history_placeholder(message):
        bot.send_message(
            message.chat.id,
            build_auction_placeholder_text(
                "📜 Історія",
                "Тут буде історія купівлі, продажу, зняття лотів і майбутня статистика цін."
            ),
            reply_markup=auction_house_kb()
        )
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def patch_handler(root):
    target = root / HANDLER_PATH
    target.parent.mkdir(exist_ok=True)

    original = target.read_text(encoding="utf-8") if target.exists() else None
    backup = make_backup(root, target) if target.exists() else None

    target.write_text(AUCTION_HANDLER_CODE.strip() + "\n", encoding="utf-8")
    return target, backup, original, True


def patch_keyboards(root):
    target = root / "keyboards.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено keyboards.py")

    original = target.read_text(encoding="utf-8")

    if "🏛️ Торговий дім" in original:
        return target, None, original, False

    backup = make_backup(root, target)
    lines = original.splitlines()

    def_index = None
    for i, line in enumerate(lines):
        if re.match(r"^def\s+city_kb\s*\(", line):
            def_index = i
            break

    if def_index is None:
        # Fallback: if city_kb not found, do not risk breaking keyboard file.
        return target, backup, original, False

    end_index = len(lines)
    for i in range(def_index + 1, len(lines)):
        if re.match(r"^def\s+", lines[i]) or re.match(r"^class\s+", lines[i]):
            end_index = i
            break

    return_index = None
    for i in range(def_index + 1, end_index):
        if lines[i].strip() == "return kb":
            return_index = i
            break

    if return_index is None:
        return target, backup, original, False

    indent_match = re.match(r"^(\s*)return kb", lines[return_index])
    indent = indent_match.group(1) if indent_match else "    "
    lines.insert(return_index, f'{indent}kb.add("🏛️ Торговий дім")')

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target, backup, original, True


def patch_main(root):
    target = root / "main.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено main.py")

    original = target.read_text(encoding="utf-8")
    text = original
    changed = False
    backup = None

    import_line = "from handlers.auction_house import register_auction_house_handlers"
    register_line = "register_auction_house_handlers(bot)"

    if import_line not in text:
        backup = backup or make_backup(root, target)
        # Insert after last handlers import if possible.
        handler_imports = list(re.finditer(r"^from handlers\.[^\n]+import[^\n]+$", text, flags=re.MULTILINE))
        if handler_imports:
            last = handler_imports[-1]
            text = text[:last.end()] + "\n" + import_line + text[last.end():]
        else:
            text = import_line + "\n" + text
        changed = True

    if register_line not in text:
        backup = backup or make_backup(root, target)
        # Prefer after guild registration, otherwise after city/start registration, otherwise before BOT STARTED print.
        candidates = [
            "register_guild_handlers(bot)",
            "register_city_handlers(bot)",
            "register_start_handlers(bot)",
        ]
        inserted = False
        for candidate in candidates:
            idx = text.find(candidate)
            if idx != -1:
                line_end = text.find("\n", idx)
                if line_end == -1:
                    line_end = len(text)
                text = text[:line_end + 1] + register_line + "\n" + text[line_end + 1:]
                inserted = True
                break

        if not inserted:
            idx = text.find('print("✅ BOT STARTED")')
            if idx == -1:
                idx = text.find("print('✅ BOT STARTED')")
            if idx != -1:
                text = text[:idx] + register_line + "\n" + text[idx:]
                inserted = True

        if not inserted:
            text = text.rstrip() + "\n" + register_line + "\n"

        changed = True

    if changed:
        target.write_text(text, encoding="utf-8")

    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_handler, patch_keyboards, patch_main]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        unique_files = []
        for file_path in changed_files:
            if file_path not in unique_files:
                unique_files.append(file_path)

        # Always compile the handler, and changed project files.
        compile_targets = set(unique_files)
        compile_targets.add(root / HANDLER_PATH)
        compile_targets.add(root / "main.py")
        compile_targets.add(root / "keyboards.py")

        for file_path in compile_targets:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                if original is None:
                    file_path.unlink(missing_ok=True)
                else:
                    file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_2_auction_house_ui.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.2 Auction House UI застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- handlers/auction_house.py")
    print("- головне меню 🏛️ Торговий дім")
    print("- кнопки: 🛒 Купити, ➕ Виставити товар, 📦 Мої лоти, 📬 Незабрані предмети, 💰 Завершені продажі, 📜 Історія, 🔙 Місто")
    print("- кнопку 🏛️ Торговий дім у city_kb()")
    print("- register_auction_house_handlers(bot) у main.py")
    print("- placeholder-и для наступних етапів 8.0.x")

    print("\nПісля патча:")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("python -m py_compile .\\keyboards.py")
    print("python -m py_compile .\\main.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
