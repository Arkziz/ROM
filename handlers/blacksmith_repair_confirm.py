from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def _safe_answer(bot, call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


def _get_item_name(inventory_id):
    try:
        from db import get_item_by_inventory_id_full
        item = get_item_by_inventory_id_full(inventory_id)

        if isinstance(item, dict):
            return item.get("name") or item.get("item_name") or f"Предмет #{inventory_id}"

        if item:
            return str(item)

    except Exception:
        pass

    try:
        from db import get_item_by_inventory_id
        item = get_item_by_inventory_id(inventory_id)

        if isinstance(item, dict):
            return item.get("name") or item.get("item_name") or f"Предмет #{inventory_id}"

        if item:
            return str(item)

    except Exception:
        pass

    return f"Предмет #{inventory_id}"


def _result_message(result, default_text):
    if isinstance(result, dict):
        if result.get("message"):
            return result["message"]

        if result.get("success"):
            return default_text

        return result.get("error") or result.get("reason") or "❌ Дію не виконано."

    if isinstance(result, str):
        return result

    return default_text


def _confirm_one_kb(inventory_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "✅ Підтвердити ремонт",
            callback_data=f"brc_confirm_one_{inventory_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="brc_cancel"
        )
    )
    return kb


def _confirm_all_kb():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "✅ Підтвердити ремонт всього",
            callback_data="brc_confirm_all"
        )
    )
    kb.add(
        InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="brc_cancel"
        )
    )
    return kb


def register_blacksmith_repair_confirmation_handlers(bot):
    """
    Register repair confirmation handlers before old instant repair handlers.

    Expected prompt callbacks:
    - repair_prompt_one_v3_<inventory_id>
    - brc_prompt_one_<inventory_id>
    - repair_prompt_all_v3
    - brc_prompt_all
    """

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("repair_prompt_one_v3_")
        or call.data.startswith("brc_prompt_one_")
    )
    def blacksmith_repair_prompt_one(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Не вдалося визначити предмет для ремонту."
            )
            return

        item_name = _get_item_name(inventory_id)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            f"📦 {item_name}\n\n"
            "Ви справді хочете відремонтувати цей предмет?\n\n"
            "Після підтвердження буде списано золото за ремонт."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_confirm_one_kb(inventory_id)
        )

    @bot.callback_query_handler(
        func=lambda call: call.data in ("repair_prompt_all_v3", "brc_prompt_all")
    )
    def blacksmith_repair_prompt_all(call):
        _safe_answer(bot, call)

        text = (
            "🛠️ Підтвердження ремонту всього спорядження\n\n"
            "Ви справді хочете відремонтувати все одягнене спорядження?\n\n"
            "Після підтвердження буде списано золото за ремонт усіх пошкоджених предметів."
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=_confirm_all_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("brc_confirm_one_"))
    def blacksmith_repair_confirm_one(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "❌ Не вдалося визначити предмет для ремонту."
            )
            return

        try:
            from db import repair_equipped_item
            result = repair_equipped_item(user_id, inventory_id)
        except TypeError:
            try:
                from db import repair_equipped_item
                result = repair_equipped_item(user_id=user_id, inventory_id=inventory_id)
            except Exception as error:
                bot.send_message(
                    call.message.chat.id,
                    f"❌ Помилка ремонту: {error}"
                )
                return
        except Exception as error:
            bot.send_message(
                call.message.chat.id,
                f"❌ Помилка ремонту: {error}"
            )
            return

        bot.send_message(
            call.message.chat.id,
            _result_message(result, "✅ Предмет відремонтовано.")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "brc_confirm_all")
    def blacksmith_repair_confirm_all(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id

        try:
            from db import repair_all_equipped
            result = repair_all_equipped(user_id)
        except TypeError:
            try:
                from db import repair_all_equipped
                result = repair_all_equipped(user_id=user_id)
            except Exception as error:
                bot.send_message(
                    call.message.chat.id,
                    f"❌ Помилка ремонту: {error}"
                )
                return
        except Exception as error:
            bot.send_message(
                call.message.chat.id,
                f"❌ Помилка ремонту: {error}"
            )
            return

        bot.send_message(
            call.message.chat.id,
            _result_message(result, "✅ Одягнене спорядження відремонтовано.")
        )

    @bot.callback_query_handler(func=lambda call: call.data == "brc_cancel")
    def blacksmith_repair_cancel(call):
        _safe_answer(bot, call)

        bot.send_message(
            call.message.chat.id,
            "❌ Ремонт скасовано."
        )


# ==============================
# ✅ ROM 9.0.8e BLACKSMITH REPAIR CONFIRM ITEM NAME FIX V1
# ==============================

# Fix reason:
# Confirmation message displayed the whole tuple from get_item_by_inventory_id_full(), e.g.
# [116, 413, '⚪️ Рукавиці 8 рівня', ...]
# instead of only the item name.

try:
    _blacksmith_confirm_base_get_item_name_before_tuple_fix_v1 = _get_item_name
except NameError:
    _blacksmith_confirm_base_get_item_name_before_tuple_fix_v1 = None


def _get_item_name(inventory_id):
    """Return clean item name for blacksmith repair confirmation."""

    item = None

    try:
        from db import get_item_by_inventory_id_full
        item = get_item_by_inventory_id_full(inventory_id)
    except Exception:
        item = None

    name = None

    if isinstance(item, dict):
        name = (
            item.get("name")
            or item.get("item_name")
            or item.get("raw_name")
        )
    elif isinstance(item, (list, tuple)):
        # Common tuple format in this project:
        # (inventory_id, item_id, name, type, rarity, category, slot_key, ...)
        try:
            if len(item) > 2 and isinstance(item[2], str):
                name = item[2]
        except Exception:
            name = None

    if not name:
        try:
            from db import get_item_by_inventory_id
            item = get_item_by_inventory_id(inventory_id)

            if isinstance(item, dict):
                name = item.get("name") or item.get("item_name") or item.get("raw_name")
            elif isinstance(item, (list, tuple)):
                # Usually (inventory_id, item_id, name, ...), but keep safe fallbacks.
                for index in [2, 1, 0]:
                    try:
                        if index < len(item) and isinstance(item[index], str):
                            name = item[index]
                            break
                    except Exception:
                        pass
            elif isinstance(item, str):
                name = item
        except Exception:
            pass

    if not name:
        name = f"Предмет #{inventory_id}"

    try:
        from db import get_inventory_refined_display_name
        return get_inventory_refined_display_name(inventory_id, name)
    except Exception:
        return name


# ==============================
# ✅ ROM 9.0.8f BLACKSMITH SHOW REPAIR MENU AFTER SUCCESS V1
# ==============================

# UX improvement:
# Після успішного ремонту одразу знову показуємо актуальний список предметів,
# які ще можна відремонтувати — ніби гравець повторно натиснув 🛠️ Ремонт.


def _brc_show_repair_menu_after_action_v1(bot, chat_id, user_id):
    try:
        from handlers.city import build_blacksmith_repair_text
        from keyboards import blacksmith_kb

        result = build_blacksmith_repair_text(user_id)

        if isinstance(result, tuple):
            text = result[0]
            kb = result[1] if len(result) > 1 else blacksmith_kb()
        else:
            text = result
            kb = blacksmith_kb()

        bot.send_message(chat_id, text, reply_markup=kb)
    except Exception as error:
        try:
            bot.send_message(chat_id, f"⚠️ Не вдалося оновити список ремонту: {error}")
        except Exception:
            pass


def register_blacksmith_repair_confirmation_handlers(bot):
    """
    Final repair confirmation handlers.

    Difference from previous version:
    - after successful/cancelled repair, shows fresh repair menu again.
    """

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("repair_prompt_one_v3_")
        or call.data.startswith("brc_prompt_one_")
    )
    def blacksmith_repair_prompt_one_v1(call):
        _safe_answer(bot, call)

        data = call.data or ""
        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        item_name = _get_item_name(inventory_id)

        text = (
            "🛠️ Підтвердження ремонту\n\n"
            f"📦 {item_name}\n\n"
            "Ви справді хочете відремонтувати цей предмет?\n\n"
            "Після підтвердження буде списано золото за ремонт."
        )

        bot.send_message(call.message.chat.id, text, reply_markup=_confirm_one_kb(inventory_id))

    @bot.callback_query_handler(func=lambda call: call.data in ("repair_prompt_all_v3", "brc_prompt_all"))
    def blacksmith_repair_prompt_all_v1(call):
        _safe_answer(bot, call)

        text = (
            "🛠️ Підтвердження ремонту всього спорядження\n\n"
            "Ви справді хочете відремонтувати все одягнене спорядження?\n\n"
            "Після підтвердження буде списано золото за ремонт усіх пошкоджених предметів."
        )

        bot.send_message(call.message.chat.id, text, reply_markup=_confirm_all_kb())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("brc_confirm_one_"))
    def blacksmith_repair_confirm_one_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        data = call.data or ""

        try:
            inventory_id = int(data.rsplit("_", 1)[1])
        except Exception:
            bot.send_message(call.message.chat.id, "❌ Не вдалося визначити предмет для ремонту.")
            return

        try:
            from db import repair_equipped_item
            result = repair_equipped_item(user_id, inventory_id)
        except TypeError:
            try:
                from db import repair_equipped_item
                result = repair_equipped_item(user_id=user_id, inventory_id=inventory_id)
            except Exception as error:
                bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
                return
        except Exception as error:
            bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
            return

        bot.send_message(call.message.chat.id, _result_message(result, "✅ Предмет відремонтовано."))
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "brc_confirm_all")
    def blacksmith_repair_confirm_all_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id

        try:
            from db import repair_all_equipped
            result = repair_all_equipped(user_id)
        except TypeError:
            try:
                from db import repair_all_equipped
                result = repair_all_equipped(user_id=user_id)
            except Exception as error:
                bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
                return
        except Exception as error:
            bot.send_message(call.message.chat.id, f"❌ Помилка ремонту: {error}")
            return

        bot.send_message(call.message.chat.id, _result_message(result, "✅ Одягнене спорядження відремонтовано."))
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "brc_cancel")
    def blacksmith_repair_cancel_v1(call):
        _safe_answer(bot, call)

        user_id = call.from_user.id
        bot.send_message(call.message.chat.id, "❌ Ремонт скасовано.")
        _brc_show_repair_menu_after_action_v1(bot, call.message.chat.id, user_id)

