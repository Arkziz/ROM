from pathlib import Path
from datetime import datetime
import py_compile

PATCH_NAME = "8_0_5e_auction_sell_item_review_before_price"
SYSTEM_TARGET = Path("systems") / "auction_house_system.py"
DB_TARGET = Path("db.py")
HANDLER_TARGET = Path("handlers") / "auction_house.py"
SYSTEM_MARKER = "# ✅ AUCTION HOUSE SELL REVIEW TEXT V1"
DB_MARKER = "# ✅ AUCTION HOUSE SELL REVIEW WRAPPER V1"
HANDLER_MARKER = "# ✅ AUCTION HOUSE SELL REVIEW BEFORE PRICE V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE SELL REVIEW TEXT V1
# ==============================


def build_auction_sell_item_review_text(user_id, inventory_id, category):
    """
    Builds an inventory-style preview before listing an item.

    This is for seller-side review only. It deliberately does not show player-specific
    equip warnings such as current player level or "can equip from level" messages.
    """

    category = normalize_auction_category(category)

    if category == AUCTION_CATEGORY_EQUIPMENT:
        validation = validate_inventory_item_for_auction_equipment(user_id, inventory_id)
        if not validation.get("success"):
            return validation

        snapshot = validation["snapshot"]
        try:
            snapshot = _auction_enrich_equipment_snapshot_with_runtime_details(user_id, inventory_id, snapshot)
        except Exception:
            pass

        refine_level = int(snapshot.get("refine_level", 0) or 0)
        item_type = snapshot.get("item_type") or _auction_snapshot_value(snapshot, "type", "item_type", default="")
        slot_key = snapshot.get("slot_key") or _auction_snapshot_value(snapshot, "slot_key", "slot", default="")
        level = int(snapshot.get("level", 0) or 0)

        lines = []
        lines.append("📦 Огляд товару")
        lines.append("")
        lines.append(str(snapshot.get("name") or "Предмет"))
        lines.append("")
        lines.append(_auction_inventory_style_type_line(AUCTION_CATEGORY_EQUIPMENT))
        lines.append(f"🎯 Слот: {_auction_inventory_style_slot(snapshot, slot_key, item_type)}")

        class_line = _auction_allowed_classes_line(snapshot)
        if class_line:
            lines.append(class_line)

        if level:
            lines.append(f"🏷 Рівень предмета: {level} 🔒")

        weapon_hand_line = _auction_weapon_hand_line(snapshot)
        if weapon_hand_line:
            lines.append(weapon_hand_line)

        damage_lines = _auction_inventory_style_damage_lines(snapshot)
        lines.extend(damage_lines)

        defense_lines = _auction_collect_inventory_style_defense_lines(snapshot)
        lines.extend(defense_lines)

        durability_current = snapshot.get("durability_current")
        durability_max = snapshot.get("durability_max")
        if durability_current is not None:
            lines.append(f"🧱 Міцність: {durability_current}/{durability_max}")

        bonus_lines = _auction_collect_inventory_style_bonus_lines(snapshot)
        if bonus_lines:
            lines.append("")
            lines.append("📊 Бонуси:")
            lines.extend(bonus_lines)

        if refine_level:
            lines.append("")
            lines.append(f"✨ Заточка: +{refine_level}")

        if not damage_lines and not defense_lines and not bonus_lines:
            lines.append("")
            lines.append("ℹ️ Детальні характеристики для цього предмета не знайдені у snapshot.")

        lines.append("")
        lines.append("Перевір характеристики предмета перед тим, як ввести ціну.")

        return {
            "success": True,
            "snapshot": snapshot,
            "text": "\n".join(lines),
        }

    # Stack items: potions/materials.
    snapshot_result = get_inventory_item_snapshot_for_auction(user_id, inventory_id)
    if not snapshot_result.get("success"):
        return snapshot_result

    snapshot = snapshot_result["snapshot"]

    if _auction_is_success_rune(snapshot):
        return {
            "success": False,
            "message": "❌ 💎 Руну Успіху не можна виставити на Торговий Дім.",
        }

    if not _auction_stack_category_matches(snapshot, category):
        return {
            "success": False,
            "message": "❌ Предмет не належить до обраної категорії.",
        }

    quantity = int(snapshot.get("quantity", 0) or 0)

    lines = []
    lines.append("📦 Огляд товару")
    lines.append("")
    lines.append(str(snapshot.get("name") or "Предмет"))
    lines.append("")
    lines.append(_auction_inventory_style_type_line(category))
    lines.append(f"📦 У наявності: {quantity}")

    desc_lines = _auction_collect_stack_description_lines(snapshot)
    if desc_lines:
        lines.append("")
        lines.extend(desc_lines)

    lines.append("")
    lines.append("Перевір товар перед тим, як вказати кількість для продажу.")

    return {
        "success": True,
        "snapshot": snapshot,
        "text": "\n".join(lines),
    }
'''

DB_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE SELL REVIEW WRAPPER V1
# ==============================


def build_auction_sell_item_review_text(user_id, inventory_id, category):
    from systems.auction_house_system import build_auction_sell_item_review_text as _func
    return _func(user_id=user_id, inventory_id=inventory_id, category=category)
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ AUCTION HOUSE SELL REVIEW BEFORE PRICE V1
# ==============================

AUCTION_SELL_REVIEW_STATE = {}


def _auction_clear_sell_review_state_v1(user_id):
    AUCTION_SELL_REVIEW_STATE.pop(user_id, None)
    try:
        _auction_clear_all_sell_states_v1(user_id)
    except Exception:
        pass


def auction_sell_review_kb_v1(category, inventory_id, page=0):
    kb = types.InlineKeyboardMarkup(row_width=1)

    if category == "equipment":
        kb.add(types.InlineKeyboardButton("💰 Ввести ціну", callback_data=f"ahsrp:{category}:{inventory_id}:{page}"))
    else:
        kb.add(types.InlineKeyboardButton("🔢 Вказати кількість", callback_data=f"ahsrq:{category}:{inventory_id}:{page}"))

    kb.add(types.InlineKeyboardButton("🔙 До списку предметів", callback_data=f"ah_sell_page:{category}:{page}"))
    kb.add(types.InlineKeyboardButton("❌ Скасувати", callback_data="ah_menu"))
    return kb


def _auction_send_sell_review_v1(bot, chat_id, user_id, inventory_id, category, page=0, edit_message=None):
    from db import build_auction_sell_item_review_text

    review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)
    if not review.get("success"):
        text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=page)
        bot.send_message(chat_id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
        bot.send_message(chat_id, text, reply_markup=kb)
        return

    AUCTION_SELL_REVIEW_STATE[user_id] = {
        "step": "review",
        "category": category,
        "inventory_id": inventory_id,
        "snapshot": review.get("snapshot"),
        "page": page,
    }

    kb = auction_sell_review_kb_v1(category, inventory_id, page=page)

    if edit_message is not None:
        try:
            bot.edit_message_text(review["text"], chat_id=chat_id, message_id=edit_message.message_id, reply_markup=kb)
            return
        except Exception:
            pass

    bot.send_message(chat_id, review["text"], reply_markup=kb)


def _auction_register_sell_review_before_price_handlers_v1(bot):

    @bot.message_handler(func=lambda m: m.text == AUCTION_SELL_BUTTON)
    def auction_sell_start_review_v1(message):
        user_id = message.from_user.id
        _auction_clear_sell_review_state_v1(user_id)
        AUCTION_SELL_REVIEW_STATE[user_id] = {"step": "category"}
        bot.send_message(
            message.chat.id,
            build_auction_sell_start_text_inline_v1(),
            reply_markup=auction_sell_inline_category_kb_v1(),
        )

    @bot.message_handler(func=lambda m: m.from_user.id in AUCTION_SELL_REVIEW_STATE)
    def auction_sell_review_message_router_v1(message):
        user_id = message.from_user.id
        text = message.text or ""
        state = AUCTION_SELL_REVIEW_STATE.get(user_id) or {}
        step = state.get("step")

        if text == AUCTION_BACK_TO_MENU_BUTTON:
            _auction_clear_sell_review_state_v1(user_id)
            bot.send_message(message.chat.id, build_auction_house_text(user_id), reply_markup=auction_house_kb())
            return

        if text == AUCTION_CANCEL_BUTTON:
            _auction_clear_sell_review_state_v1(user_id)
            bot.send_message(message.chat.id, "❌ Виставлення товару скасовано.", reply_markup=auction_house_kb())
            return

        if step == "category":
            if text not in AUCTION_SELL_INLINE_CATEGORY_BUTTONS:
                bot.send_message(message.chat.id, "Оберіть категорію кнопкою нижче.", reply_markup=auction_sell_inline_category_kb_v1())
                return

            category = AUCTION_SELL_INLINE_CATEGORY_BUTTONS[text]
            state.update({"step": "item_inline", "category": category, "page": 0})
            AUCTION_SELL_REVIEW_STATE[user_id] = state
            list_text, kb = build_auction_sell_inline_list_text_v1(user_id, category, page=0)
            bot.send_message(message.chat.id, list_text, reply_markup=kb)
            return

        if step == "quantity":
            category = state.get("category")
            inventory_id = state.get("inventory_id")

            try:
                quantity = int(text)
            except Exception:
                bot.send_message(message.chat.id, "❌ Введіть кількість числом.")
                return

            from db import validate_inventory_stack_item_for_auction
            validation = validate_inventory_stack_item_for_auction(
                user_id=user_id,
                inventory_id=inventory_id,
                category=category,
                quantity=quantity,
            )

            if not validation.get("success"):
                bot.send_message(message.chat.id, validation.get("message", "❌ Некоректна кількість."))
                return

            state.update({
                "step": "price",
                "quantity": quantity,
                "snapshot": validation["snapshot"],
            })
            AUCTION_SELL_REVIEW_STATE[user_id] = state
            bot.send_message(message.chat.id, build_auction_stack_price_prompt_v2(validation["snapshot"], quantity), reply_markup=types.ReplyKeyboardRemove())
            return

        if step == "price":
            from db import validate_auction_price
            price_result = validate_auction_price(text)
            if not price_result.get("success"):
                bot.send_message(message.chat.id, price_result.get("message", "❌ Некоректна ціна.") + "\n\nСпробуйте ще раз або напишіть ❌ Скасувати.", reply_markup=auction_sell_confirm_kb())
                return

            state["step"] = "confirm"
            state["price"] = price_result["price"]
            AUCTION_SELL_REVIEW_STATE[user_id] = state

            if state.get("category") == "equipment":
                confirm_text = build_auction_sell_confirm_text(state["snapshot"], price_result["price"])
            else:
                confirm_text = build_auction_stack_confirm_text_v2(state["snapshot"], state.get("quantity", 1), price_result["price"])

            bot.send_message(message.chat.id, confirm_text, reply_markup=auction_sell_confirm_kb())
            return

        if step == "confirm":
            if text != AUCTION_CONFIRM_LIST_BUTTON:
                bot.send_message(message.chat.id, "Підтвердіть виставлення або скасуйте дію.", reply_markup=auction_sell_confirm_kb())
                return

            category = state.get("category")

            if category == "equipment":
                from db import create_equipment_auction_lot
                result = create_equipment_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    price=state.get("price"),
                )
            else:
                from db import create_stack_auction_lot
                result = create_stack_auction_lot(
                    user_id=user_id,
                    inventory_id=state.get("inventory_id"),
                    category=category,
                    quantity=state.get("quantity"),
                    price=state.get("price"),
                )

            _auction_clear_sell_review_state_v1(user_id)

            if not result.get("success"):
                bot.send_message(message.chat.id, result.get("message", "❌ Не вдалося створити лот."), reply_markup=auction_house_kb())
                return

            bot.send_message(
                message.chat.id,
                (
                    "✅ Лот виставлено на продаж!\n\n"
                    f"📦 {result.get('item_name')}\n"
                    f"💰 Ціна: {result.get('price')} золота\n"
                    "⏳ Термін: 7 днів\n\n"
                    "Предмет перенесено з інвентаря до Торгового Дому."
                ),
                reply_markup=auction_house_kb(),
            )
            return

        bot.send_message(message.chat.id, "Оберіть предмет зі списку або поверніться до Торгового Дому.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ah_sell_item:"))
    def auction_sell_review_item_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        _auction_send_sell_review_v1(
            bot=bot,
            chat_id=call.message.chat.id,
            user_id=user_id,
            inventory_id=inventory_id,
            category=category,
            page=page,
            edit_message=call.message,
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ahsrp:"))
    def auction_sell_review_price_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        from db import build_auction_sell_item_review_text
        review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not review.get("success"):
            bot.send_message(call.message.chat.id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
            return

        AUCTION_SELL_REVIEW_STATE[user_id] = {
            "step": "price",
            "category": category,
            "inventory_id": inventory_id,
            "snapshot": review["snapshot"],
            "quantity": 1,
            "page": page,
        }
        bot.send_message(call.message.chat.id, build_auction_sell_price_prompt(review["snapshot"]), reply_markup=types.ReplyKeyboardRemove())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("ahsrq:"))
    def auction_sell_review_quantity_callback_v1(call):
        user_id = call.from_user.id
        parts = call.data.split(":")
        category = parts[1]
        inventory_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0

        from db import build_auction_sell_item_review_text
        review = build_auction_sell_item_review_text(user_id=user_id, inventory_id=inventory_id, category=category)

        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass

        if not review.get("success"):
            bot.send_message(call.message.chat.id, review.get("message", "❌ Предмет не можна виставити."), reply_markup=auction_house_kb())
            return

        AUCTION_SELL_REVIEW_STATE[user_id] = {
            "step": "quantity",
            "category": category,
            "inventory_id": inventory_id,
            "snapshot": review["snapshot"],
            "page": page,
        }
        bot.send_message(call.message.chat.id, build_auction_stack_quantity_prompt_v2(review["snapshot"], category), reply_markup=types.ReplyKeyboardRemove())


try:
    _auction_base_register_handlers_before_sell_review_v1 = register_auction_house_handlers
except NameError:
    _auction_base_register_handlers_before_sell_review_v1 = None


def register_auction_house_handlers(bot):
    # Review handlers must be registered before previous sell inline handlers.
    _auction_register_sell_review_before_price_handlers_v1(bot)

    if _auction_base_register_handlers_before_sell_review_v1:
        _auction_base_register_handlers_before_sell_review_v1(bot)
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_once(root, rel_path, marker, append_code):
    target = root / rel_path
    if not target.exists():
        raise SystemExit(f"❌ Не знайдено {rel_path}")

    original = target.read_text(encoding="utf-8")
    if marker in original:
        return target, None, original, False

    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + append_code + "\n", encoding="utf-8")
    return target, backup, original, True


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        patches = [
            (SYSTEM_TARGET, SYSTEM_MARKER, SYSTEM_APPEND),
            (DB_TARGET, DB_MARKER, DB_APPEND),
            (HANDLER_TARGET, HANDLER_MARKER, HANDLER_APPEND),
        ]

        for rel_path, marker, append_code in patches:
            file_path, backup, original, changed = append_once(root, rel_path, marker, append_code)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        compile_targets = [
            root / SYSTEM_TARGET,
            root / DB_TARGET,
            root / HANDLER_TARGET,
        ]
        for file_path in compile_targets:
            py_compile.compile(str(file_path), doraise=True)

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_8_0_5e_auction_sell_item_review_before_price.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 8.0.5e Auction sell item review before price застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- після вибору предмета показується 📦 Огляд товару")
    print("- для спорядження: характеристики як у картці предмета без player-specific попереджень")
    print("- для матеріалів/зілля: показ кількості, типу та опису")
    print("- кнопка 💰 Ввести ціну для спорядження")
    print("- кнопка 🔢 Вказати кількість для стекових предметів")
    print("- кнопка 🔙 До списку предметів")
    print("- тільки після огляду гравець вводить ціну")

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\auction_house_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\auction_house.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
