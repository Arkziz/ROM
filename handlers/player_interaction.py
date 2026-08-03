# -*- coding: utf-8 -*-
"""Map-based player discovery and interaction menu, ROM 12.2.0."""
from __future__ import annotations

from telebot import types

from systems.player_interaction_system import (
    create_player_interaction_request,
    respond_to_player_interaction_request,
    cancel_player_trade,
    get_online_players_in_same_location,
    get_public_player_interaction_profile,
    touch_player_activity,
    get_player_trade_editor_state,
    get_tradeable_inventory_for_trade,
    set_player_trade_item_offer,
    remove_player_trade_item_offer,
    set_player_trade_gold_offer,
)

PLAYER_LIST_BUTTON = "👥 Гравці локації"
PAGE_SIZE = 8


def _safe_answer(bot, call, text=None, show_alert=False):
    try:
        bot.answer_callback_query(call.id, text=text, show_alert=show_alert)
    except Exception:
        pass


def _location_label(value):
    values = {
        "start_path": "Початок Шляху",
        "dark_forest": "Темний Бір",
    }
    return values.get(str(value), str(value).replace("_", " ").title())


def build_location_players_text(result):
    location = _location_label(result.get("location", ""))
    total = int(result.get("total", 0))
    if total <= 0:
        return (
            "👥 <b>Гравці локації</b>\n\n"
            f"📍 Локація: {location}\n"
            "🟢 Активних гравців: 0\n\n"
            "Зараз у цій локації немає інших активних гравців."
        )
    return (
        "👥 <b>Гравці локації</b>\n\n"
        f"📍 Локація: {location}\n"
        f"🟢 Активних гравців: {total}\n\n"
        "Оберіть гравця:"
    )


def build_location_players_kb(result):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for player in result.get("players", []):
        name = str(player.get("character_name") or "Гравець")
        level = player.get("level")
        suffix = f", {level} рівень" if level is not None else ""
        kb.add(types.InlineKeyboardButton(
            text=f"🟢 {name}{suffix}",
            callback_data=f"pi:player:{int(player['user_id'])}",
        ))
    nav = []
    page = int(result.get("page", 0))
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=f"pi:list:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton("➡️", callback_data=f"pi:list:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.row(types.InlineKeyboardButton("🔄 Оновити", callback_data=f"pi:list:{page}"))
    kb.row(types.InlineKeyboardButton("🔙 До Мапи", callback_data="pi:back:map"))
    return kb


def _profile_text(profile):
    location = _location_label(profile.get("current_location", ""))
    level = profile.get("level")
    class_name = profile.get("character_class") or "не визначено"
    return (
        "👤 <b>Взаємодія з гравцем</b>\n\n"
        f"Ім’я: {profile.get('character_name') or 'Гравець'}\n"
        f"Рівень: {level if level is not None else 'не визначено'}\n"
        f"Клас: {class_name}\n"
        f"Локація: {location}\n"
        "Статус: 🟢 Онлайн"
    )


def _profile_kb(target_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🤝 Запропонувати обмін", callback_data=f"pi:trade:{target_id}"))
    kb.add(types.InlineKeyboardButton("⚔️ Викликати на дуель", callback_data=f"pi:duel:{target_id}"))
    kb.add(types.InlineKeyboardButton("🔙 До гравців локації", callback_data="pi:list:0"))
    return kb




# ROM 12.4.1 TRADE CANCEL CALLBACK ROUTING HOTFIX
def _is_trade_request_callback(call):
    """Match only pi:trade:<target_user_id>, never pi:trade:cancel:<trade_id>."""
    data = str(getattr(call, "data", ""))
    parts = data.split(":")
    return len(parts) == 3 and parts[0] == "pi" and parts[1] == "trade" and parts[2].isdigit()



# ROM 12.6.0 PLAYER TRADE OFFER EDITOR UI
TRADE_EDITOR_PAGE_SIZE = 8


def _trade_offer_name(offer):
    snapshot = offer.get("snapshot") or {}
    return str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{offer.get('item_id')}")


def _trade_offer_lines(offers):
    lines = []
    for offer in offers:
        if offer.get("asset_type") == "gold":
            lines.append(f"• 💰 {float(offer.get('gold_amount') or 0):.2f} золота")
        else:
            lines.append(f"• {_trade_offer_name(offer)} x{int(offer.get('quantity') or 1)}")
    return lines or ["• нічого не додано"]


def _trade_editor_text(state):
    return (
        "🤝 <b>Прямий обмін</b>\n\n"
        "<b>Ваша пропозиція:</b>\n" + "\n".join(_trade_offer_lines(state.get("own_offers", []))) +
        "\n\n<b>Пропозиція іншого гравця:</b>\n" + "\n".join(_trade_offer_lines(state.get("other_offers", []))) +
        "\n\nРедагування пропозиції скидає готовність обох гравців."
    )


def _trade_editor_kb(trade_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("➕ Додати предмет", callback_data=f"pi:te:list:{trade_id}:0"))
    kb.row(
        types.InlineKeyboardButton("💰 +1", callback_data=f"pi:te:gold:{trade_id}:1"),
        types.InlineKeyboardButton("💰 +10", callback_data=f"pi:te:gold:{trade_id}:10"),
    )
    kb.row(
        types.InlineKeyboardButton("💰 -1", callback_data=f"pi:te:gold:{trade_id}:-1"),
        types.InlineKeyboardButton("🧹 Золото 0", callback_data=f"pi:te:gold0:{trade_id}"),
    )
    kb.row(types.InlineKeyboardButton("🔄 Оновити", callback_data=f"pi:te:open:{trade_id}"))
    kb.row(types.InlineKeyboardButton("❌ Скасувати обмін", callback_data=f"pi:trade:cancel:{trade_id}"))
    return kb


def _trade_inventory_text(result):
    return f"➕ <b>Додати предмет</b>\n\nДоступних предметів: {int(result.get('total', 0))}\nОберіть предмет:"


def _trade_inventory_kb(result):
    trade_id = int(result["trade_id"]); page = int(result.get("page", 0))
    kb = types.InlineKeyboardMarkup(row_width=1)
    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name = str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{snapshot.get('item_id')}")
        available = int(item.get("available_quantity") or 1)
        kb.add(types.InlineKeyboardButton(
            f"{name} (доступно {available})",
            callback_data=f"pi:te:item:{trade_id}:{int(item['inventory_id'])}:{page}",
        ))
    nav = []
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=f"pi:te:list:{trade_id}:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton("➡️", callback_data=f"pi:te:list:{trade_id}:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.row(types.InlineKeyboardButton("🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb


def _trade_item_kb(trade_id, inventory_id, quantity, page=0):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(
        types.InlineKeyboardButton("➖", callback_data=f"pi:te:set:{trade_id}:{inventory_id}:{max(0, quantity-1)}:{page}"),
        types.InlineKeyboardButton(f"x{quantity}", callback_data=f"pi:te:open:{trade_id}"),
        types.InlineKeyboardButton("➕", callback_data=f"pi:te:set:{trade_id}:{inventory_id}:{quantity+1}:{page}"),
    )
    kb.row(types.InlineKeyboardButton("🗑️ Прибрати", callback_data=f"pi:te:remove:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton("🔙 До предметів", callback_data=f"pi:te:list:{trade_id}:{page}"))
    return kb


def _send_trade_editor(bot, chat_id, user_id, trade_id, edit_message=None):
    state = get_player_trade_editor_state(trade_id, user_id)
    if not state.get("success"):
        text = "ℹ️ Обмін уже неактивний або недоступний."
        if edit_message:
            _safe_edit_message_text(bot, text, chat_id, edit_message)
        else:
            bot.send_message(chat_id, text)
        return
    text = _trade_editor_text(state); kb = _trade_editor_kb(trade_id)
    if edit_message:
        _safe_edit_message_text(bot, text, chat_id, edit_message, parse_mode="HTML", reply_markup=kb)
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

def register_player_interaction_handlers(bot):
    @bot.message_handler(func=lambda message: getattr(message, "text", None) == PLAYER_LIST_BUTTON)
    def show_location_players(message):
        user_id = int(message.from_user.id)
        touch_player_activity(user_id)
        result = get_online_players_in_same_location(user_id, page=0, page_size=PAGE_SIZE)
        if not result.get("success"):
            bot.send_message(message.chat.id, "❌ Не вдалося визначити поточну локацію персонажа.")
            return
        bot.send_message(
            message.chat.id,
            build_location_players_text(result),
            parse_mode="HTML",
            reply_markup=build_location_players_kb(result),
        )

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:list:"))
    def location_players_page(call):
        _safe_answer(bot, call)
        user_id = int(call.from_user.id)
        touch_player_activity(user_id)
        try:
            page = max(0, int(str(call.data).rsplit(":", 1)[1]))
        except (TypeError, ValueError):
            page = 0
        result = get_online_players_in_same_location(user_id, page=page, page_size=PAGE_SIZE)
        if not result.get("success"):
            _safe_edit_message_text(bot, "❌ Не вдалося визначити поточну локацію персонажа.", call.message.chat.id, call.message.message_id)
            return
        _safe_edit_message_text(bot, 
            build_location_players_text(result),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=build_location_players_kb(result),
        )

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:player:"))
    def location_player_profile(call):
        _safe_answer(bot, call)
        viewer_id = int(call.from_user.id)
        try:
            target_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError):
            return
        profile = get_public_player_interaction_profile(viewer_id, target_id)
        if not profile.get("success"):
            reason = profile.get("reason")
            messages = {
                "player_offline": "❌ Гравець більше не перебуває онлайн.",
                "different_location": "❌ Гравець уже залишив цю локацію.",
                "self_target": "❌ Не можна взаємодіяти із власним персонажем.",
            }
            _safe_answer(bot, call, messages.get(reason, "❌ Гравець недоступний."), True)
            return
        _safe_edit_message_text(bot, 
            _profile_text(profile),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=_profile_kb(target_id),
        )

    # ROM 12.3.1 TRADE REQUEST SENDER FEEDBACK HOTFIX
    @bot.callback_query_handler(func=_is_trade_request_callback)
    def trade_request(call):
        # Answer the callback once to stop Telegram's loading spinner. Final
        # success/failure feedback is sent as a normal visible chat message.
        _safe_answer(bot, call)
        try:
            target_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError):
            bot.send_message(call.message.chat.id, "❌ Гравець недоступний.")
            return

        result = create_player_interaction_request(
            int(call.from_user.id), target_id, "trade", pve_busy_checker=_possible_pve_busy
        )
        if not result.get("success"):
            bot.send_message(
                call.message.chat.id,
                _interaction_failure_message(result.get("reason")),
            )
            return

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.row(
            types.InlineKeyboardButton("✅ Прийняти", callback_data=f"pi:req:accept:{result['request_id']}:1"),
            types.InlineKeyboardButton("❌ Відхилити", callback_data=f"pi:req:decline:{result['request_id']}:1"),
        )
        bot.send_message(
            target_id,
            "🤝 <b>Запрошення на обмін</b>\n\n"
            f"Гравець {result['initiator_name']} пропонує прямий обмін.\n"
            "Запрошення діє 2 хвилини.",
            parse_mode="HTML",
            reply_markup=kb,
        )
        bot.send_message(
            call.message.chat.id,
            "✅ <b>Запит на обмін відправлено</b>\n\n"
            f"Гравець: {result['recipient_name']}\n"
            "Очікуємо відповідь протягом 2 хвилин.",
            parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith(("pi:req:accept:", "pi:req:decline:")))
    def trade_request_response(call):
        parts = str(call.data).split(":")
        if len(parts) != 5:
            return
        action = parts[2]
        try:
            request_id = int(parts[3]); revision = int(parts[4])
        except (TypeError, ValueError):
            return
        result = respond_to_player_interaction_request(
            request_id, int(call.from_user.id), action,
            expected_revision=revision, pve_busy_checker=_possible_pve_busy,
        )
        if not result.get("success"):
            _safe_answer(bot, call, _interaction_failure_message(result.get("reason")), True)
            return
        if result.get("status") == "declined":
            _safe_edit_message_text(bot, "❌ Запрошення на обмін відхилено.", call.message.chat.id, call.message.message_id)
            try:
                bot.send_message(int(result["initiator_user_id"]), "❌ Запрошення на обмін відхилено.")
            except Exception:
                pass
            return
        trade = result.get("trade") or {}
        trade_id = trade.get("trade_id") or (trade.get("trade") or {}).get("id")
        if not trade_id:
            _safe_answer(bot, call, "❌ Не вдалося створити сесію обміну.", True)
            return
        text = "✅ Запрошення прийнято.\n\nСесію обміну створено на 10 хвилин."
        _safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id)
        # ROM 12.6.4a: immediately replace the recipient's persistent gameplay
        # keyboard before the trade editor is sent.
        bot.send_message(
            call.message.chat.id,
            "🤝 Режим обміну активовано.",
            reply_markup=player_trade_active_reply_kb_12_6_4(),
        )
        _send_trade_editor(bot, call.message.chat.id, int(call.from_user.id), int(trade_id))
        try:
            initiator_id = int(result["initiator_user_id"])
            bot.send_message(initiator_id, text)
            # The initiator must receive the same keyboard replacement at the
            # same moment, without waiting for a blocked gameplay action.
            bot.send_message(
                initiator_id,
                "🤝 Режим обміну активовано.",
                reply_markup=player_trade_active_reply_kb_12_6_4(),
            )
            _send_trade_editor(bot, initiator_id, initiator_id, int(trade_id))
        except Exception:
            pass

    # ROM 12.4.0 PLAYER TRADE DATABASE AND HISTORY FOUNDATION
    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:trade:cancel:"))
    def cancel_trade_foundation(call):
        _safe_answer(bot, call)
        try:
            trade_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError):
            return
        result = cancel_player_trade(trade_id, int(call.from_user.id))
        if not result.get("success"):
            bot.send_message(call.message.chat.id, "ℹ️ Обмін уже неактивний або був скасований раніше.")
            return
        own_text = "❌ Обмін скасовано.\n\n✅ Обидва гравці знову доступні для нового обміну."
        _safe_edit_message_text(bot, own_text, call.message.chat.id, call.message.message_id)
        other = int(result["recipient_user_id"]) if int(call.from_user.id) == int(result["initiator_user_id"]) else int(result["initiator_user_id"])
        try:
            bot.send_message(other, "❌ Інший гравець скасував обмін.\n\n✅ Знову можна надсилати й отримувати запити на обмін.")
        except Exception:
            pass


    # ROM 12.6.0 PLAYER TRADE OFFER EDITOR UI
    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:te:open:"))
    def trade_editor_open(call):
        _safe_answer(bot, call)
        try: trade_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError): return
        _send_trade_editor(bot, call.message.chat.id, int(call.from_user.id), trade_id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:te:list:"))
    def trade_editor_list(call):
        _safe_answer(bot, call)
        parts = str(call.data).split(":")
        try: trade_id, page = int(parts[3]), max(0, int(parts[4]))
        except (IndexError, TypeError, ValueError): return
        result = get_tradeable_inventory_for_trade(trade_id, int(call.from_user.id), page=page, page_size=TRADE_EDITOR_PAGE_SIZE)
        if not result.get("success"):
            _safe_answer(bot, call, "Обмін уже недоступний.", True); return
        _safe_edit_message_text(bot, _trade_inventory_text(result), call.message.chat.id, call.message.message_id,
                                parse_mode="HTML", reply_markup=_trade_inventory_kb(result))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:te:item:"))
    def trade_editor_item(call):
        _safe_answer(bot, call)
        parts = str(call.data).split(":")
        try: trade_id, inventory_id, page = int(parts[3]), int(parts[4]), int(parts[5])
        except (IndexError, TypeError, ValueError): return
        state = get_player_trade_editor_state(trade_id, int(call.from_user.id))
        if not state.get("success"): return
        offer = next((x for x in state.get("own_offers", []) if x.get("inventory_id") == inventory_id), None)
        if offer is None:
            added = set_player_trade_item_offer(trade_id, int(call.from_user.id), inventory_id, 1)
            if not added.get("success"):
                _safe_answer(bot, call, added.get("message") or "Не вдалося додати предмет.", True); return
            state = get_player_trade_editor_state(trade_id, int(call.from_user.id))
            offer = next((x for x in state.get("own_offers", []) if x.get("inventory_id") == inventory_id), None)
        quantity = int((offer or {}).get("quantity") or 1)
        snapshot = (offer or {}).get("snapshot") or {}
        name = snapshot.get("item_name") or f"Предмет #{inventory_id}"
        _safe_edit_message_text(bot, f"📦 <b>{name}</b>\n\nКількість у пропозиції: {quantity}",
                                call.message.chat.id, call.message.message_id, parse_mode="HTML",
                                reply_markup=_trade_item_kb(trade_id, inventory_id, quantity, page))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:te:set:"))
    def trade_editor_set_item(call):
        parts = str(call.data).split(":")
        try: trade_id, inventory_id, quantity, page = map(int, parts[3:7])
        except (TypeError, ValueError): return
        result = set_player_trade_item_offer(trade_id, int(call.from_user.id), inventory_id, quantity)
        if not result.get("success"):
            _safe_answer(bot, call, result.get("message") or "Не вдалося змінити предмет.", True); return
        _safe_answer(bot, call, "Пропозицію оновлено.")
        if quantity <= 0:
            listing = get_tradeable_inventory_for_trade(trade_id, int(call.from_user.id), page=page, page_size=TRADE_EDITOR_PAGE_SIZE)
            _safe_edit_message_text(bot, _trade_inventory_text(listing), call.message.chat.id, call.message.message_id,
                                    parse_mode="HTML", reply_markup=_trade_inventory_kb(listing)); return
        _safe_edit_message_text(bot, f"📦 Кількість у пропозиції: {quantity}", call.message.chat.id,
                                call.message.message_id, reply_markup=_trade_item_kb(trade_id, inventory_id, quantity, page))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:te:remove:"))
    def trade_editor_remove_item(call):
        parts = str(call.data).split(":")
        try: trade_id, inventory_id, page = map(int, parts[3:6])
        except (TypeError, ValueError): return
        result = remove_player_trade_item_offer(trade_id, int(call.from_user.id), inventory_id)
        if not result.get("success"):
            _safe_answer(bot, call, "Предмет уже відсутній у пропозиції.", True); return
        _safe_answer(bot, call, "Предмет прибрано.")
        listing = get_tradeable_inventory_for_trade(trade_id, int(call.from_user.id), page=page, page_size=TRADE_EDITOR_PAGE_SIZE)
        _safe_edit_message_text(bot, _trade_inventory_text(listing), call.message.chat.id, call.message.message_id,
                                parse_mode="HTML", reply_markup=_trade_inventory_kb(listing))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith(("pi:te:gold:", "pi:te:gold0:")))
    def trade_editor_gold(call):
        parts = str(call.data).split(":")
        try:
            trade_id = int(parts[3])
            delta = 0.0 if parts[2] == "gold0" else float(parts[4])
        except (IndexError, TypeError, ValueError): return
        state = get_player_trade_editor_state(trade_id, int(call.from_user.id))
        if not state.get("success"): return
        current = next((float(x.get("gold_amount") or 0) for x in state.get("own_offers", []) if x.get("asset_type") == "gold"), 0.0)
        amount = 0.0 if parts[2] == "gold0" else max(0.0, current + delta)
        result = set_player_trade_gold_offer(trade_id, int(call.from_user.id), amount)
        if not result.get("success"):
            _safe_answer(bot, call, result.get("message") or "Не вдалося змінити золото.", True); return
        _safe_answer(bot, call, "Золото у пропозиції оновлено.")
        _send_trade_editor(bot, call.message.chat.id, int(call.from_user.id), trade_id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:duel:"))
    def duel_placeholder(call):
        _safe_answer(bot, call, "🔒 Дуелі будуть доступні в майбутньому PvP-етапі.", True)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")) == "pi:back:map")
    def back_to_map(call):
        _safe_answer(bot, call)
        bot.delete_message(call.message.chat.id, call.message.message_id)

# ROM 12.2.1 MAP REFRESH AND KEYBOARD HOTFIX
def _safe_edit_message_text(bot, *args, **kwargs):
    """Ignore only Telegram's harmless 400 'message is not modified'."""
    try:
        return bot.edit_message_text(*args, **kwargs)
    except Exception as exc:
        text = str(exc).lower()
        if "message is not modified" in text:
            return None
        raise

# ROM 12.3.0 PLAYER INTERACTION REQUESTS
def _interaction_failure_message(reason):
    return {
        "player_not_found": "❌ Гравець більше недоступний.",
        "player_offline": "❌ Один із гравців більше не перебуває онлайн.",
        "different_location": "❌ Гравці вже не перебувають в одній локації.",
        "player_busy": "❌ Один із гравців уже зайнятий іншою взаємодією.",
        "player_in_battle": "❌ Обмін неможливий, поки один із гравців перебуває в бою.",
        "request_expired": "⌛ Запрошення вже прострочене.",
        "stale_revision": "⌛ Це запрошення вже неактуальне.",
        "wrong_actor": "❌ Це запрошення призначене іншому гравцеві.",
        "request_not_pending": "ℹ️ Запрошення вже було оброблене.",
    }.get(reason, "❌ Не вдалося виконати дію із запрошенням.")


def _possible_pve_busy(user_id):
    """Best-effort adapter over the existing in-memory PvE implementation."""
    try:
        import handlers.combat as combat_module
    except Exception:
        return False
    explicit = getattr(combat_module, "is_player_in_active_combat", None)
    if callable(explicit):
        try: return bool(explicit(int(user_id)))
        except Exception: return False
    uid=int(user_id)
    for name,value in vars(combat_module).items():
        low=name.lower()
        if not isinstance(value,dict) or not any(token in low for token in ("battle","combat","fight")):
            continue
        if uid in value or str(uid) in value:
            return True
    return False

# ROM 12.6.1 PLAYER TRADE OFFER EDITOR UX
from systems.player_interaction_system import (
    add_all_available_to_trade_offer,
    get_item_trade_policy,
    get_trade_offer_entry,
)

def _trade_ux_offer_name(offer):
    snapshot = offer.get("snapshot") or {}
    return str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{offer.get('item_id')}")


def _trade_ux_is_equipment(snapshot):
    snapshot = snapshot or {}
    category = str(snapshot.get("category") or "").strip().lower()
    return category in ("equipment", "weapon", "armor", "jewelry") or snapshot.get("durability") is not None or snapshot.get("max_durability") is not None


def _trade_editor_kb(trade_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("➕ Додати предмет", callback_data=f"pi:teux:list:{trade_id}:0"),
        types.InlineKeyboardButton("✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("💰 +1", callback_data=f"pi:te:gold:{trade_id}:1"),
        types.InlineKeyboardButton("💰 +10", callback_data=f"pi:te:gold:{trade_id}:10"),
    )
    kb.row(
        types.InlineKeyboardButton("💰 -1", callback_data=f"pi:te:gold:{trade_id}:-1"),
        types.InlineKeyboardButton("🧹 Золото 0", callback_data=f"pi:te:gold0:{trade_id}"),
    )
    kb.row(types.InlineKeyboardButton("🔄 Оновити", callback_data=f"pi:te:open:{trade_id}"))
    kb.row(types.InlineKeyboardButton("❌ Скасувати обмін", callback_data=f"pi:trade:cancel:{trade_id}"))
    return kb


def _trade_ux_inventory_kb(result):
    trade_id = int(result["trade_id"]); page = int(result.get("page", 0))
    kb = types.InlineKeyboardMarkup(row_width=1)
    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name = str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{snapshot.get('item_id')}")
        remaining = int(item.get("available_quantity") or 0)
        suffix = "" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name + suffix,
            callback_data=f"pi:teux:add:{trade_id}:{int(item['inventory_id'])}:{page}",
        ))
    nav = []
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton("⬅️", callback_data=f"pi:teux:list:{trade_id}:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton("➡️", callback_data=f"pi:teux:list:{trade_id}:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.row(types.InlineKeyboardButton("✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb


def _trade_ux_mine_text(state):
    offers = state.get("own_offers", [])
    if not offers:
        return "✏️ <b>Моя пропозиція</b>\n\nВи ще не додали предметів або золота."
    return "✏️ <b>Моя пропозиція</b>\n\nОберіть позицію для редагування:"


def _trade_ux_mine_kb(state):
    trade_id = int(state["trade"]["id"])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for offer in state.get("own_offers", []):
        if offer.get("asset_type") == "gold":
            kb.add(types.InlineKeyboardButton(
                f"💰 Золото: {float(offer.get('gold_amount') or 0):.2f}",
                callback_data=f"pi:teux:gold:{trade_id}"))
        else:
            kb.add(types.InlineKeyboardButton(
                f"{_trade_ux_offer_name(offer)} x{int(offer.get('quantity') or 1)}",
                callback_data=f"pi:teux:edit:{trade_id}:{int(offer['inventory_id'])}"))
    if not state.get("own_offers"):
        kb.row(types.InlineKeyboardButton("➕ Додати предмет", callback_data=f"pi:teux:list:{trade_id}:0"))
    kb.row(types.InlineKeyboardButton("🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb


def _trade_ux_stack_kb(trade_id, inventory_id, quantity, maximum, back_callback):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(
        types.InlineKeyboardButton("➖", callback_data=f"pi:teux:set:{trade_id}:{inventory_id}:{max(0, quantity-1)}"),
        types.InlineKeyboardButton(f"x{quantity}", callback_data=back_callback),
        types.InlineKeyboardButton("➕", callback_data=f"pi:teux:set:{trade_id}:{inventory_id}:{min(maximum, quantity+1)}"),
    )
    if quantity < maximum:
        kb.row(types.InlineKeyboardButton("📦 Додати все", callback_data=f"pi:teux:all:{trade_id}:{inventory_id}"))
    kb.row(types.InlineKeyboardButton("🗑️ Прибрати", callback_data=f"pi:teux:remove:{trade_id}:{inventory_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До моєї пропозиції", callback_data=f"pi:teux:mine:{trade_id}"))
    return kb


def _trade_ux_equipment_kb(trade_id, inventory_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(types.InlineKeyboardButton("🗑️ Прибрати з пропозиції", callback_data=f"pi:teux:remove:{trade_id}:{inventory_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До моєї пропозиції", callback_data=f"pi:teux:mine:{trade_id}"))
    return kb


def _trade_ux_show_mine(bot, call, trade_id):
    state = get_player_trade_editor_state(trade_id, int(call.from_user.id))
    if not state.get("success"):
        _safe_answer(bot, call, "Обмін уже недоступний.", True); return
    _safe_edit_message_text(bot, _trade_ux_mine_text(state), call.message.chat.id, call.message.message_id,
                            parse_mode="HTML", reply_markup=_trade_ux_mine_kb(state))


def _register_player_trade_offer_editor_ux_handlers(bot):
    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:list:"))
    def trade_ux_list(call):
        _safe_answer(bot, call)
        try:
            _, _, _, trade_id, page = str(call.data).split(":")
            trade_id=int(trade_id); page=max(0,int(page))
        except (TypeError, ValueError): return
        result=get_tradeable_inventory_for_trade(trade_id,int(call.from_user.id),page=page,page_size=TRADE_EDITOR_PAGE_SIZE)
        if not result.get("success"):
            _safe_answer(bot,call,"Обмін уже недоступний.",True); return
        text=(f"➕ <b>Додати предмет</b>\n\nДоступних позицій: {int(result.get('total',0))}\n"
              + ("Оберіть предмет:" if result.get("items") else "Усі доступні предмети вже додано до пропозиції."))
        _safe_edit_message_text(bot,text,call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_inventory_kb(result))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:add:"))
    def trade_ux_add(call):
        try:
            _,_,_,trade_id,inventory_id,page=str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError,ValueError): return
        result=get_tradeable_inventory_for_trade(trade_id,int(call.from_user.id),page=page,page_size=TRADE_EDITOR_PAGE_SIZE)
        item=next((x for x in result.get("items",[]) if int(x["inventory_id"])==inventory_id),None)
        if not item:
            _safe_answer(bot,call,"Предмет уже повністю додано або недоступний.",True); return
        if item.get("is_equipment"):
            added=set_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id,1)
            if not added.get("success"):
                _safe_answer(bot,call,added.get("message") or "Не вдалося додати предмет.",True); return
            _safe_answer(bot,call,"Предмет додано до пропозиції.")
            refreshed=get_tradeable_inventory_for_trade(trade_id,int(call.from_user.id),page=page,page_size=TRADE_EDITOR_PAGE_SIZE)
            text=(f"➕ <b>Додати предмет</b>\n\nДоступних позицій: {int(refreshed.get('total',0))}\n"
                  + ("Оберіть предмет:" if refreshed.get("items") else "Усі доступні предмети вже додано до пропозиції."))
            _safe_edit_message_text(bot,text,call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_inventory_kb(refreshed)); return
        existing=get_trade_offer_entry(trade_id,int(call.from_user.id),inventory_id)
        quantity=int((existing or {}).get("quantity") or 0)
        if quantity <= 0:
            added=set_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id,1)
            if not added.get("success"):
                _safe_answer(bot,call,added.get("message") or "Не вдалося додати предмет.",True); return
            quantity=1
        maximum=int(item.get("total_available_quantity") or quantity)
        name=str((item.get("snapshot") or {}).get("item_name") or f"Предмет #{inventory_id}")
        _safe_answer(bot,call,"Стек додано до пропозиції.")
        _safe_edit_message_text(bot,f"📦 <b>{name}</b>\n\nКількість у пропозиції: {quantity}\nМаксимум доступно: {maximum}",call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_stack_kb(trade_id,inventory_id,quantity,maximum,f"pi:teux:list:{trade_id}:{page}"))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:mine:"))
    def trade_ux_mine(call):
        _safe_answer(bot,call)
        try: trade_id=int(str(call.data).rsplit(":",1)[1])
        except (TypeError,ValueError): return
        _trade_ux_show_mine(bot,call,trade_id)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:edit:"))
    def trade_ux_edit(call):
        _safe_answer(bot,call)
        try:
            _,_,_,trade_id,inventory_id=str(call.data).split(":"); trade_id=int(trade_id); inventory_id=int(inventory_id)
        except (TypeError,ValueError): return
        offer=get_trade_offer_entry(trade_id,int(call.from_user.id),inventory_id)
        if not offer:
            _safe_answer(bot,call,"Позицію вже прибрано.",True); return
        snapshot=offer.get("snapshot") or {}; name=_trade_ux_offer_name(offer); quantity=int(offer.get("quantity") or 1)
        if _trade_ux_is_equipment(snapshot):
            text=f"📦 <b>{name}</b>\n\nПредмет додано до вашої пропозиції."
            kb=_trade_ux_equipment_kb(trade_id,inventory_id)
        else:
            policy=get_item_trade_policy(int(call.from_user.id),inventory_id,1,trade_id=trade_id)
            maximum=int(policy.get("available_quantity") or quantity)
            text=f"📦 <b>{name}</b>\n\nКількість у пропозиції: {quantity}\nМаксимум доступно: {maximum}"
            kb=_trade_ux_stack_kb(trade_id,inventory_id,quantity,maximum,f"pi:teux:mine:{trade_id}")
        _safe_edit_message_text(bot,text,call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:set:"))
    def trade_ux_set(call):
        try:
            _,_,_,trade_id,inventory_id,quantity=str(call.data).split(":"); trade_id=int(trade_id); inventory_id=int(inventory_id); quantity=int(quantity)
        except (TypeError,ValueError): return
        if quantity <= 0:
            result=remove_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id)
            if not result.get("success"):
                _safe_answer(bot,call,"Позицію вже прибрано.",True); return
            _safe_answer(bot,call,"Предмет прибрано."); _trade_ux_show_mine(bot,call,trade_id); return
        result=set_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id,quantity)
        if not result.get("success"):
            _safe_answer(bot,call,result.get("message") or "Не вдалося змінити кількість.",True); return
        _safe_answer(bot,call,"Кількість оновлено.")
        offer=get_trade_offer_entry(trade_id,int(call.from_user.id),inventory_id); policy=get_item_trade_policy(int(call.from_user.id),inventory_id,1,trade_id=trade_id)
        maximum=int(policy.get("available_quantity") or quantity); name=_trade_ux_offer_name(offer or {})
        _safe_edit_message_text(bot,f"📦 <b>{name}</b>\n\nКількість у пропозиції: {quantity}\nМаксимум доступно: {maximum}",call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_stack_kb(trade_id,inventory_id,quantity,maximum,f"pi:teux:mine:{trade_id}"))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:all:"))
    def trade_ux_all(call):
        try:
            _,_,_,trade_id,inventory_id=str(call.data).split(":"); trade_id=int(trade_id); inventory_id=int(inventory_id)
        except (TypeError,ValueError): return
        result=add_all_available_to_trade_offer(trade_id,int(call.from_user.id),inventory_id)
        if not result.get("success"):
            _safe_answer(bot,call,result.get("message") or "Не вдалося додати весь стек.",True); return
        _safe_answer(bot,call,"Увесь доступний стек додано.")
        _trade_ux_show_mine(bot,call,trade_id)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:remove:"))
    def trade_ux_remove(call):
        try:
            _,_,_,trade_id,inventory_id=str(call.data).split(":"); trade_id=int(trade_id); inventory_id=int(inventory_id)
        except (TypeError,ValueError): return
        result=remove_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id)
        if not result.get("success"):
            _safe_answer(bot,call,"Позицію вже прибрано.",True); return
        _safe_answer(bot,call,"Предмет прибрано."); _trade_ux_show_mine(bot,call,trade_id)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:teux:gold:"))
    def trade_ux_gold(call):
        _safe_answer(bot,call)
        try: trade_id=int(str(call.data).rsplit(":",1)[1])
        except (TypeError,ValueError): return
        state=get_player_trade_editor_state(trade_id,int(call.from_user.id))
        amount=next((float(x.get("gold_amount") or 0) for x in state.get("own_offers",[]) if x.get("asset_type")=="gold"),0.0)
        kb=types.InlineKeyboardMarkup(row_width=2)
        kb.row(types.InlineKeyboardButton("💰 -1",callback_data=f"pi:te:gold:{trade_id}:-1"),types.InlineKeyboardButton("💰 +1",callback_data=f"pi:te:gold:{trade_id}:1"))
        kb.row(types.InlineKeyboardButton("🧹 Золото 0",callback_data=f"pi:te:gold0:{trade_id}"))
        kb.row(types.InlineKeyboardButton("🔙 До моєї пропозиції",callback_data=f"pi:teux:mine:{trade_id}"))
        _safe_edit_message_text(bot,f"💰 <b>Золото у пропозиції</b>\n\nПоточна сума: {amount:.2f}",call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=kb)


_trade_ux_base_register_player_interaction_handlers = register_player_interaction_handlers

def register_player_interaction_handlers(bot):
    # UX callbacks must be registered before the 12.6.0 editor callbacks.
    _register_player_trade_offer_editor_ux_handlers(bot)
    return _trade_ux_base_register_player_interaction_handlers(bot)

# ROM 12.6.2 PLAYER TRADE ITEM PREVIEW AND WALLET UX
from systems.player_interaction_system import (
    get_player_trade_wallet_state,
    get_trade_item_preview,
)

_TRADE_RARITY_LABELS_12_6_2 = {
    "common": "Звичайний", "uncommon": "Незвичайний",
    "rare": "Рідкісний", "epic": "Епічний",
}


def _trade_money_12_6_2(value):
    return f"{float(value or 0):.2f}"


def _trade_snapshot_lines_12_6_2(snapshot, include_quantity=False):
    snapshot = snapshot or {}
    lines = []
    category = str(snapshot.get("category") or "").strip()
    rarity = str(snapshot.get("rarity") or "").strip().lower()
    level = snapshot.get("level") or snapshot.get("item_level")
    durability = snapshot.get("durability")
    max_durability = snapshot.get("max_durability")
    refine = int(snapshot.get("refine_level") or 0)
    if category:
        lines.append(f"Категорія: {category}")
    if rarity:
        lines.append(f"Рідкість: {_TRADE_RARITY_LABELS_12_6_2.get(rarity, rarity)}")
    if level is not None:
        lines.append(f"Рівень предмета: {level}")
    if durability is not None:
        max_text = max_durability if max_durability is not None else 100
        lines.append(f"Міцність: {durability}/{max_text}")
    if refine > 0:
        lines.append(f"Заточка: +{refine}")
    runes = list(snapshot.get("runes") or [])
    if runes:
        rune_names = ", ".join(str(x.get("rune_name") or x.get("rune_item_id")) for x in runes)
        lines.append(f"Вставлені руни: {rune_names}")
    if include_quantity and snapshot.get("quantity") is not None:
        lines.append(f"Усього в інвентарі: {int(snapshot.get('quantity') or 0)}")
    return lines


def _trade_editor_text(state):
    wallet = get_player_trade_wallet_state(
        int(state["trade"]["id"]), int(state["viewer_user_id"]))
    wallet_lines = ""
    if wallet.get("success"):
        wallet_lines = (
            f"\n\n💰 Ваше золото: {_trade_money_12_6_2(wallet['wallet_gold'])}"
            f"\n💰 У пропозиції: {_trade_money_12_6_2(wallet['offered_gold'])}"
            f"\n💰 Доступний залишок: {_trade_money_12_6_2(wallet['remaining_gold'])}"
        )
    return (
        "🤝 <b>Прямий обмін</b>\n\n"
        "<b>Ваша пропозиція:</b>\n" + "\n".join(_trade_offer_lines(state.get("own_offers", []))) +
        wallet_lines +
        "\n\n<b>Пропозиція іншого гравця:</b>\n" + "\n".join(_trade_offer_lines(state.get("other_offers", []))) +
        "\n\nРедагування пропозиції скидає готовність обох гравців."
    )


def _trade_preview_text_12_6_2(preview):
    snapshot = preview.get("snapshot") or {}
    name = str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{preview.get('inventory_id')}")
    lines = [f"📦 <b>{name}</b>", ""]
    lines.extend(_trade_snapshot_lines_12_6_2(snapshot, include_quantity=preview.get("is_stack")))
    if preview.get("is_equipment"):
        lines.extend(["", "Додати цей предмет до пропозиції?"])
    else:
        offered = int(preview.get("offered_quantity") or 0)
        maximum = int(preview.get("maximum_quantity") or 0)
        remaining = max(0, maximum - offered)
        lines.extend([
            "", f"Уже в пропозиції: {offered}",
            f"Можна додати ще: {remaining}",
            "", "Змініть кількість кнопками нижче або додайте весь доступний стек.",
        ])
    return "\n".join(lines)


def _trade_preview_equipment_kb_12_6_2(trade_id, inventory_id, page):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.row(types.InlineKeyboardButton(
        "✅ Додати предмет", callback_data=f"pi:tep:addone:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До предметів", callback_data=f"pi:teux:list:{trade_id}:{page}"))
    return kb


def _trade_preview_stack_kb_12_6_2(preview, page):
    trade_id = int(preview["trade_id"]); inventory_id = int(preview["inventory_id"])
    quantity = int(preview.get("offered_quantity") or 0)
    maximum = int(preview.get("maximum_quantity") or quantity)
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(
        types.InlineKeyboardButton("➖", callback_data=f"pi:tep:set:{trade_id}:{inventory_id}:{max(0, quantity-1)}:{page}"),
        types.InlineKeyboardButton(f"x{quantity}", callback_data=f"pi:tep:view:{trade_id}:{inventory_id}:{page}"),
        types.InlineKeyboardButton("➕", callback_data=f"pi:tep:set:{trade_id}:{inventory_id}:{min(maximum, quantity+1)}:{page}"),
    )
    if quantity < maximum:
        kb.row(types.InlineKeyboardButton(
            "📦 Додати все доступне", callback_data=f"pi:tep:all:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До предметів", callback_data=f"pi:teux:list:{trade_id}:{page}"))
    return kb


def _trade_show_preview_12_6_2(bot, call, trade_id, inventory_id, page):
    preview = get_trade_item_preview(trade_id, int(call.from_user.id), inventory_id)
    if not preview.get("success"):
        _safe_answer(bot, call, preview.get("message") or "Предмет недоступний.", True)
        return
    kb = (_trade_preview_equipment_kb_12_6_2(trade_id, inventory_id, page)
          if preview.get("is_equipment") else _trade_preview_stack_kb_12_6_2(preview, page))
    _safe_edit_message_text(
        bot, _trade_preview_text_12_6_2(preview), call.message.chat.id,
        call.message.message_id, parse_mode="HTML", reply_markup=kb)


def _trade_gold_text_12_6_2(trade_id, user_id):
    wallet = get_player_trade_wallet_state(trade_id, user_id)
    if not wallet.get("success"):
        return "💰 <b>Золото у пропозиції</b>\n\nОбмін уже недоступний."
    return (
        "💰 <b>Золото у пропозиції</b>\n\n"
        f"У гаманці: {_trade_money_12_6_2(wallet['wallet_gold'])}\n"
        f"У пропозиції: {_trade_money_12_6_2(wallet['offered_gold'])}\n"
        f"Ще можна додати: {_trade_money_12_6_2(wallet['remaining_gold'])}"
    )


def _register_trade_preview_wallet_handlers_12_6_2(bot):
    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:tep:view:"))
    def trade_preview_view(call):
        _safe_answer(bot, call)
        try:
            _, _, _, trade_id, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        _trade_show_preview_12_6_2(bot, call, trade_id, inventory_id, page)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:tep:addone:"))
    def trade_preview_add_one(call):
        try:
            _, _, _, trade_id, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        result=set_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id,1)
        if not result.get("success"):
            _safe_answer(bot,call,result.get("message") or "Не вдалося додати предмет.",True); return
        _safe_answer(bot,call,"Предмет додано до пропозиції.")
        listing=get_tradeable_inventory_for_trade(trade_id,int(call.from_user.id),page=page,page_size=TRADE_EDITOR_PAGE_SIZE)
        text=(f"➕ <b>Додати предмет</b>\n\nДоступних позицій: {int(listing.get('total',0))}\n"
              + ("Оберіть предмет:" if listing.get("items") else "Усі доступні предмети вже додано до пропозиції."))
        _safe_edit_message_text(bot,text,call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_inventory_kb(listing))

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:tep:set:"))
    def trade_preview_set(call):
        try:
            _, _, _, trade_id, inventory_id, quantity, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); quantity=int(quantity); page=int(page)
        except (TypeError, ValueError): return
        if quantity <= 0:
            existing=get_trade_offer_entry(trade_id,int(call.from_user.id),inventory_id)
            result=remove_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id) if existing else {"success":True}
        else:
            result=set_player_trade_item_offer(trade_id,int(call.from_user.id),inventory_id,quantity)
        if not result.get("success"):
            _safe_answer(bot,call,result.get("message") or "Не вдалося змінити кількість.",True); return
        _safe_answer(bot,call,"Кількість оновлено.")
        _trade_show_preview_12_6_2(bot,call,trade_id,inventory_id,page)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("pi:tep:all:"))
    def trade_preview_all(call):
        try:
            _, _, _, trade_id, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        result=add_all_available_to_trade_offer(trade_id,int(call.from_user.id),inventory_id)
        if not result.get("success"):
            _safe_answer(bot,call,result.get("message") or "Не вдалося додати весь стек.",True); return
        _safe_answer(bot,call,"Увесь доступний стек додано.")
        listing=get_tradeable_inventory_for_trade(trade_id,int(call.from_user.id),page=page,page_size=TRADE_EDITOR_PAGE_SIZE)
        text=(f"➕ <b>Додати предмет</b>\n\nДоступних позицій: {int(listing.get('total',0))}\n"
              + ("Оберіть предмет:" if listing.get("items") else "Усі доступні предмети вже додано до пропозиції."))
        _safe_edit_message_text(bot,text,call.message.chat.id,call.message.message_id,parse_mode="HTML",reply_markup=_trade_ux_inventory_kb(listing))


# Override the 12.6.1 add-list buttons: selecting an item opens preview and
# does not immediately add it to the offer.
def _trade_ux_inventory_kb(result):
    trade_id=int(result["trade_id"]); page=int(result.get("page",0))
    kb=types.InlineKeyboardMarkup(row_width=1)
    for item in result.get("items",[]):
        snapshot=item.get("snapshot") or {}
        name=str(snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{snapshot.get('item_id')}")
        remaining=int(item.get("available_quantity") or 0)
        suffix="" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name+suffix, callback_data=f"pi:tep:view:{trade_id}:{int(item['inventory_id'])}:{page}"))
    nav=[]
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton("⬅️",callback_data=f"pi:teux:list:{trade_id}:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton("➡️",callback_data=f"pi:teux:list:{trade_id}:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(types.InlineKeyboardButton("✏️ Моя пропозиція",callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До обміну",callback_data=f"pi:te:open:{trade_id}"))
    return kb


# Override the 12.6.1 wallet editor with live wallet/offered/remaining values.
def _trade_gold_editor_kb_12_6_2(trade_id):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("💰 -1",callback_data=f"pi:te:gold:{trade_id}:-1"),types.InlineKeyboardButton("💰 +1",callback_data=f"pi:te:gold:{trade_id}:1"))
    kb.row(types.InlineKeyboardButton("💰 +10",callback_data=f"pi:te:gold:{trade_id}:10"),types.InlineKeyboardButton("🧹 Золото 0",callback_data=f"pi:te:gold0:{trade_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До моєї пропозиції",callback_data=f"pi:teux:mine:{trade_id}"))
    return kb


_trade_preview_base_register_player_interaction_handlers = register_player_interaction_handlers

def register_player_interaction_handlers(bot):
    _register_trade_preview_wallet_handlers_12_6_2(bot)
    return _trade_preview_base_register_player_interaction_handlers(bot)

# ROM 12.6.3 PLAYER TRADE PREVIEW DETAILS AND AMOUNT INPUT
from systems.player_interaction_system import parse_trade_item_quantity_input, parse_trade_gold_amount_input
from data.equipment_profiles import EQUIPMENT_SLOTS, ARMOR_TYPE_LABELS, ITEM_SUBTYPE_LABELS

TRADE_AMOUNT_INPUT_STATE_12_6_3={}
TRADE_AMOUNT_INPUT_TTL_SECONDS_12_6_3=300
_TRADE_CATEGORY_LABELS_12_6_3={
    "equipment":"Спорядження","weapon":"Зброя","armor":"Броня",
    "jewelry":"Біжутерія","material":"Матеріал","special_material":"Особливий матеріал",
    "rune":"Руна","potion":"Зілля","consumable":"Витратний предмет",
}
_TRADE_ATTACK_LABELS_12_6_3={"physical":"Фізична","magical":"Магічна","defense":"Захисна"}
_TRADE_STAT_LABELS_12_6_3={"bonus_str":"Сила","bonus_dex":"Спритність","bonus_int":"Інтелект","bonus_wis":"Мудрість","bonus_sta":"Витривалість","pdef":"Фізичний захист","mdef":"Магічний захист"}

def _trade_category_ua_12_6_3(value):
    return _TRADE_CATEGORY_LABELS_12_6_3.get(str(value or "").strip().lower(),"Предмет")

def _trade_snapshot_lines_12_6_2(snapshot,include_quantity=False):
    snapshot=snapshot or {}; lines=[]
    lines.append(f"Категорія: {_trade_category_ua_12_6_3(snapshot.get('category'))}")
    rarity=str(snapshot.get("rarity") or "").strip().lower()
    if rarity: lines.append(f"Рідкість: {_TRADE_RARITY_LABELS_12_6_2.get(rarity,rarity)}")
    level=snapshot.get("item_level") if snapshot.get("item_level") is not None else snapshot.get("level")
    if level is not None: lines.append(f"Рівень предмета: {level}")
    slot=str(snapshot.get("slot_key") or "")
    if slot: lines.append(f"Слот: {EQUIPMENT_SLOTS.get(slot,slot)}")
    armor=str(snapshot.get("armor_type") or "")
    if armor: lines.append(f"Тип броні: {ARMOR_TYPE_LABELS.get(armor,armor)}")
    subtype=str(snapshot.get("item_subtype") or "")
    if subtype: lines.append(f"Тип предмета: {ITEM_SUBTYPE_LABELS.get(subtype,subtype)}")
    attack=str(snapshot.get("weapon_attack_type") or "")
    if attack: lines.append(f"Тип атаки: {_TRADE_ATTACK_LABELS_12_6_3.get(attack,attack)}")
    hands=int(snapshot.get("weapon_hands") or 0)
    if hands: lines.append(f"Кількість рук: {hands}")
    pmin=int(snapshot.get("weapon_min_damage") or 0); pmax=int(snapshot.get("weapon_max_damage") or 0)
    mmin=int(snapshot.get("weapon_min_magic_damage") or 0); mmax=int(snapshot.get("weapon_max_magic_damage") or 0)
    if pmin or pmax: lines.append(f"Фізична шкода: {pmin}-{pmax}")
    if mmin or mmax: lines.append(f"Магічна шкода: {mmin}-{mmax}")
    durability=snapshot.get("durability"); max_durability=snapshot.get("max_durability")
    if durability is not None: lines.append(f"Міцність: {durability}/{max_durability if max_durability is not None else 100}")
    refine=int(snapshot.get("refine_level") or 0)
    if refine: lines.append(f"Заточка: +{refine}")
    stats=[]
    for key,label in _TRADE_STAT_LABELS_12_6_3.items():
        value=int(snapshot.get(key) or 0)
        if value: stats.append(f"• {label}: +{value}")
    if stats: lines.extend(["","Характеристики:",*stats])
    runes=list(snapshot.get("runes") or [])
    if runes:
        lines.extend(["","Вставлені руни:"]+[f"• {x.get('rune_name') or x.get('rune_item_id')}" for x in runes])
    if include_quantity and snapshot.get("quantity") is not None:
        lines.append(f"Усього в інвентарі: {int(snapshot.get('quantity') or 0)}")
    return lines

def _trade_editor_kb(trade_id):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("➕ Додати предмет",callback_data=f"pi:teux:list:{trade_id}:0"),
        types.InlineKeyboardButton("💰 Додати золото",callback_data=f"pi:tea:gold:{trade_id}"),
    )
    kb.row(types.InlineKeyboardButton("✏️ Моя пропозиція",callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(
        types.InlineKeyboardButton("🔄 Оновити",callback_data=f"pi:te:open:{trade_id}"),
        types.InlineKeyboardButton("❌ Скасувати обмін",callback_data=f"pi:trade:cancel:{trade_id}"),
    )
    return kb

def _trade_amount_cancel_kb_12_6_3():
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("❌ Скасувати введення")
    return kb

def _trade_gold_menu_kb_12_6_3(trade_id):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("➖ 1",callback_data=f"pi:tea:gdelta:{trade_id}:-1"),types.InlineKeyboardButton("➕ 1",callback_data=f"pi:tea:gdelta:{trade_id}:1"))
    kb.row(types.InlineKeyboardButton("➖ 10",callback_data=f"pi:tea:gdelta:{trade_id}:-10"),types.InlineKeyboardButton("➕ 10",callback_data=f"pi:tea:gdelta:{trade_id}:10"))
    kb.row(types.InlineKeyboardButton("⌨️ Ввести суму",callback_data=f"pi:tea:ginput:{trade_id}"))
    kb.row(types.InlineKeyboardButton("🧹 Очистити",callback_data=f"pi:tea:gclear:{trade_id}"))
    kb.row(types.InlineKeyboardButton("🔙 До обміну",callback_data=f"pi:te:open:{trade_id}"))
    return kb

def _trade_preview_stack_kb_12_6_2(preview,page):
    trade_id=int(preview["trade_id"]); inventory_id=int(preview["inventory_id"])
    quantity=int(preview.get("offered_quantity") or 0); maximum=int(preview.get("maximum_quantity") or quantity)
    kb=types.InlineKeyboardMarkup(row_width=3)
    kb.row(types.InlineKeyboardButton("➖",callback_data=f"pi:tep:set:{trade_id}:{inventory_id}:{max(0,quantity-1)}:{page}"),types.InlineKeyboardButton(f"x{quantity}",callback_data=f"pi:tep:view:{trade_id}:{inventory_id}:{page}"),types.InlineKeyboardButton("➕",callback_data=f"pi:tep:set:{trade_id}:{inventory_id}:{min(maximum,quantity+1)}:{page}"))
    if quantity<maximum: kb.row(types.InlineKeyboardButton("📦 Додати все доступне",callback_data=f"pi:tep:all:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton("⌨️ Ввести кількість",callback_data=f"pi:tea:qinput:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton("🔙 До предметів",callback_data=f"pi:teux:list:{trade_id}:{page}"))
    return kb

def _trade_register_amount_input_12_6_3(bot):
    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("pi:tea:gold:"))
    def open_gold(c):
        _safe_answer(bot,c)
        trade_id=int(str(c.data).rsplit(":",1)[1])
        _safe_edit_message_text(bot,_trade_gold_text_12_6_2(trade_id,int(c.from_user.id)),c.message.chat.id,c.message.message_id,parse_mode="HTML",reply_markup=_trade_gold_menu_kb_12_6_3(trade_id))

    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("pi:tea:gdelta:"))
    def gold_delta(c):
        parts=str(c.data).split(":"); trade_id=int(parts[3]); delta=float(parts[4])
        wallet=get_player_trade_wallet_state(trade_id,int(c.from_user.id))
        target=max(0.0,float(wallet.get("offered_gold") or 0)+delta)
        result=set_player_trade_gold_offer(trade_id,int(c.from_user.id),target)
        if not result.get("success"): _safe_answer(bot,c,result.get("message") or "Не вдалося змінити золото.",True); return
        _safe_answer(bot,c,"Суму оновлено.")
        _safe_edit_message_text(bot,_trade_gold_text_12_6_2(trade_id,int(c.from_user.id)),c.message.chat.id,c.message.message_id,parse_mode="HTML",reply_markup=_trade_gold_menu_kb_12_6_3(trade_id))

    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("pi:tea:gclear:"))
    def gold_clear(c):
        trade_id=int(str(c.data).rsplit(":",1)[1]); result=set_player_trade_gold_offer(trade_id,int(c.from_user.id),0)
        _safe_answer(bot,c,"Золото очищено." if result.get("success") else "Не вдалося очистити золото.",not result.get("success"))
        _safe_edit_message_text(bot,_trade_gold_text_12_6_2(trade_id,int(c.from_user.id)),c.message.chat.id,c.message.message_id,parse_mode="HTML",reply_markup=_trade_gold_menu_kb_12_6_3(trade_id))

    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("pi:tea:ginput:"))
    def gold_input(c):
        _safe_answer(bot,c); trade_id=int(str(c.data).rsplit(":",1)[1])
        TRADE_AMOUNT_INPUT_STATE_12_6_3[int(c.from_user.id)]={"mode":"gold","trade_id":trade_id,"created_at":datetime.now().timestamp()}
        wallet=get_player_trade_wallet_state(trade_id,int(c.from_user.id))
        bot.send_message(c.message.chat.id,f"⌨️ Введення золота\n\nУ гаманці: {_trade_money_12_6_2(wallet.get('wallet_gold'))}\nЗараз у пропозиції: {_trade_money_12_6_2(wallet.get('offered_gold'))}\n\nВведіть загальну суму золота для пропозиції.",reply_markup=_trade_amount_cancel_kb_12_6_3())

    @bot.callback_query_handler(func=lambda c:str(getattr(c,"data","")).startswith("pi:tea:qinput:"))
    def quantity_input(c):
        _safe_answer(bot,c); parts=str(c.data).split(":"); trade_id=int(parts[3]); inventory_id=int(parts[4]); page=int(parts[5])
        preview=get_trade_item_preview(trade_id,int(c.from_user.id),inventory_id)
        TRADE_AMOUNT_INPUT_STATE_12_6_3[int(c.from_user.id)]={"mode":"quantity","trade_id":trade_id,"inventory_id":inventory_id,"page":page,"created_at":datetime.now().timestamp()}
        name=(preview.get("snapshot") or {}).get("item_name") or f"Предмет #{inventory_id}"
        bot.send_message(c.message.chat.id,f"⌨️ Введення кількості\n\nПредмет: {name}\nУже в пропозиції: {int(preview.get('offered_quantity') or 0)}\nДоступно максимум: {int(preview.get('maximum_quantity') or 0)}\n\nВведіть загальну кількість у пропозиції.",reply_markup=_trade_amount_cancel_kb_12_6_3())

    @bot.message_handler(func=lambda m:int(getattr(getattr(m,"from_user",None),"id",0)) in TRADE_AMOUNT_INPUT_STATE_12_6_3)
    def amount_message(m):
        uid=int(m.from_user.id); state=TRADE_AMOUNT_INPUT_STATE_12_6_3.get(uid) or {}
        if m.text=="❌ Скасувати введення":
            # ROM 12.6.4d: cancelling amount input must return to the active
            # trade UI. ReplyKeyboardRemove previously removed the only valid
            # trade navigation button and left both participants effectively
            # trapped behind the navigation lock.
            TRADE_AMOUNT_INPUT_STATE_12_6_3.pop(uid, None)
            bot.send_message(
                m.chat.id,
                "Введення скасовано.",
                reply_markup=player_trade_active_reply_kb_12_6_4(),
            )
            active_trade = get_active_player_trade(uid)
            if active_trade:
                _send_trade_editor(
                    bot, m.chat.id, uid, int(active_trade["id"])
                )
            else:
                bot.send_message(
                    m.chat.id,
                    "ℹ️ Активного обміну вже немає.",
                    reply_markup=main_kb(),
                )
            return
        if datetime.now().timestamp()-float(state.get("created_at") or 0)>TRADE_AMOUNT_INPUT_TTL_SECONDS_12_6_3:
            TRADE_AMOUNT_INPUT_STATE_12_6_3.pop(uid,None); bot.send_message(m.chat.id,"Час введення минув.",reply_markup=types.ReplyKeyboardRemove()); return
        trade_id=int(state["trade_id"])
        if state.get("mode")=="gold":
            wallet=get_player_trade_wallet_state(trade_id,uid); parsed=parse_trade_gold_amount_input(m.text,wallet.get("wallet_gold"))
            if not parsed.get("success"): bot.send_message(m.chat.id,"❌ "+parsed["message"],reply_markup=_trade_amount_cancel_kb_12_6_3()); return
            result=set_player_trade_gold_offer(trade_id,uid,parsed["gold_amount"])
        else:
            inventory_id=int(state["inventory_id"]); preview=get_trade_item_preview(trade_id,uid,inventory_id)
            parsed=parse_trade_item_quantity_input(m.text,preview.get("maximum_quantity"))
            if not parsed.get("success"): bot.send_message(m.chat.id,"❌ "+parsed["message"],reply_markup=_trade_amount_cancel_kb_12_6_3()); return
            quantity=int(parsed["quantity"])
            existing=get_trade_offer_entry(trade_id,uid,inventory_id)
            result=(remove_player_trade_item_offer(trade_id,uid,inventory_id) if quantity==0 and existing else ({"success":True} if quantity==0 else set_player_trade_item_offer(trade_id,uid,inventory_id,quantity)))
        if not result.get("success"): bot.send_message(m.chat.id,"❌ "+str(result.get("message") or "Не вдалося зберегти значення."),reply_markup=_trade_amount_cancel_kb_12_6_3()); return
        TRADE_AMOUNT_INPUT_STATE_12_6_3.pop(uid,None)
        bot.send_message(m.chat.id,"✅ Значення оновлено.",reply_markup=types.ReplyKeyboardRemove())
        _send_trade_editor(bot,m.chat.id,uid,trade_id)

_trade_amount_base_register_12_6_3=register_player_interaction_handlers
def register_player_interaction_handlers(bot):
    _trade_register_amount_input_12_6_3(bot)
    return _trade_amount_base_register_12_6_3(bot)

# ROM 12.6.3a PLAYER TRADE DATETIME AND EQUIPMENT TYPE HOTFIX
# 12.6.3 uses datetime.now() in manual amount input handlers.
from datetime import datetime

_TRADE_ARMOR_SLOT_KEYS_12_6_3A = frozenset((
    "helmet", "shoulders", "chest", "gloves", "legs", "boots",
))


def _trade_add_list_display_name_12_6_3a(snapshot):
    """Build the add-list name and restore canonical [Armor type] display."""
    snapshot = snapshot or {}
    name = str(
        snapshot.get("item_name")
        or snapshot.get("name")
        or f"Предмет #{snapshot.get('item_id')}"
    )
    slot_key = str(snapshot.get("slot_key") or "").strip().lower()
    armor_type = str(snapshot.get("armor_type") or "").strip().lower()
    if slot_key in _TRADE_ARMOR_SLOT_KEYS_12_6_3A and armor_type:
        armor_label = ARMOR_TYPE_LABELS.get(armor_type, armor_type)
        typed_suffix = f"[{armor_label}]"
        if typed_suffix.casefold() not in name.casefold():
            level_token = str(snapshot.get("item_level") or snapshot.get("level") or "").strip()
            if level_token:
                marker = f" {level_token} рівня"
                if marker in name:
                    return name.replace(marker, f" {typed_suffix}{marker}", 1)
            return f"{name} {typed_suffix}"
    return name


# Final override of the add-list keyboard. It preserves 12.6.2 preview routing
# and 12.6.1 remaining-quantity behavior, changing only the visible item name.
def _trade_ux_inventory_kb(result):
    trade_id = int(result["trade_id"])
    page = int(result.get("page", 0))
    kb = types.InlineKeyboardMarkup(row_width=1)
    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name = _trade_add_list_display_name_12_6_3a(snapshot)
        remaining = int(item.get("available_quantity") or 0)
        suffix = "" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name + suffix,
            callback_data=f"pi:tep:view:{trade_id}:{int(item['inventory_id'])}:{page}",
        ))
    nav = []
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton(
            "⬅️", callback_data=f"pi:teux:list:{trade_id}:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton(
            "➡️", callback_data=f"pi:teux:list:{trade_id}:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.row(types.InlineKeyboardButton(
        "✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb

# ROM 12.6.3b PLAYER TRADE EQUIPMENT USAGE AND QUANTITY LABELS
_TRADE_MAIN_HAND_WEAPON_SUBTYPES_12_6_3B = frozenset((
    "sword_1h", "dagger_1h", "wand_1h",
    "sword_2h", "staff_2h", "bow_2h", "crossbow_2h",
))
_TRADE_OFF_HAND_WEAPON_SUBTYPES_12_6_3B = frozenset((
    "dagger", "offhand_dagger", "dagger_offhand",
))
_TRADE_OFF_HAND_ITEM_SUBTYPES_12_6_3B = frozenset((
    "shield", "talisman",
))


def _trade_equipment_usage_label_12_6_3b(snapshot):
    """Return a player-facing usage label only for hand-slot equipment."""
    snapshot = snapshot or {}
    slot_key = str(snapshot.get("slot_key") or "").strip().lower()
    subtype = str(snapshot.get("item_subtype") or "").strip().lower()
    try:
        weapon_hands = int(snapshot.get("weapon_hands") or 0)
    except (TypeError, ValueError):
        weapon_hands = 0

    if slot_key == "main_hand" or subtype in _TRADE_MAIN_HAND_WEAPON_SUBTYPES_12_6_3B:
        if weapon_hands >= 2 or subtype.endswith("_2h"):
            return "Дворучна зброя"
        return "Одноручна зброя"

    if slot_key == "off_hand":
        if subtype in _TRADE_OFF_HAND_WEAPON_SUBTYPES_12_6_3B:
            return "Зброя для другої руки"
        if subtype in _TRADE_OFF_HAND_ITEM_SUBTYPES_12_6_3B or subtype:
            return "Предмет для другої руки"
        return "Предмет для другої руки"

    return ""


def _trade_snapshot_lines_12_6_2(snapshot, include_quantity=False):
    """Final 12.6.3b preview formatter.

    Stackable items show `Кількість: N`. Technical weapon_hands defaults are
    ignored outside main/off-hand equipment. Weapons show readable usage.
    """
    snapshot = snapshot or {}
    lines = []
    lines.append(f"Категорія: {_trade_category_ua_12_6_3(snapshot.get('category'))}")

    rarity = str(snapshot.get("rarity") or "").strip().lower()
    if rarity:
        lines.append(f"Рідкість: {_TRADE_RARITY_LABELS_12_6_2.get(rarity, rarity)}")

    level = snapshot.get("item_level")
    if level is None:
        level = snapshot.get("level")
    if level is not None:
        lines.append(f"Рівень предмета: {level}")

    slot_key = str(snapshot.get("slot_key") or "").strip().lower()
    if slot_key:
        lines.append(f"Слот: {EQUIPMENT_SLOTS.get(slot_key, slot_key)}")

    armor_type = str(snapshot.get("armor_type") or "").strip().lower()
    if armor_type:
        lines.append(f"Тип броні: {ARMOR_TYPE_LABELS.get(armor_type, armor_type)}")

    subtype = str(snapshot.get("item_subtype") or "").strip().lower()
    if subtype:
        lines.append(f"Тип предмета: {ITEM_SUBTYPE_LABELS.get(subtype, subtype)}")

    usage = _trade_equipment_usage_label_12_6_3b(snapshot)
    if usage:
        lines.append(f"Використання: {usage}")

    attack_type = str(snapshot.get("weapon_attack_type") or "").strip().lower()
    if attack_type:
        lines.append(f"Тип атаки: {_TRADE_ATTACK_LABELS_12_6_3.get(attack_type, attack_type)}")

    physical_min = int(snapshot.get("weapon_min_damage") or 0)
    physical_max = int(snapshot.get("weapon_max_damage") or 0)
    magic_min = int(snapshot.get("weapon_min_magic_damage") or 0)
    magic_max = int(snapshot.get("weapon_max_magic_damage") or 0)
    if physical_min or physical_max:
        lines.append(f"Фізична шкода: {physical_min}-{physical_max}")
    if magic_min or magic_max:
        lines.append(f"Магічна шкода: {magic_min}-{magic_max}")

    durability = snapshot.get("durability")
    max_durability = snapshot.get("max_durability")
    if durability is not None:
        lines.append(
            f"Міцність: {durability}/{max_durability if max_durability is not None else 100}"
        )

    refine_level = int(snapshot.get("refine_level") or 0)
    if refine_level:
        lines.append(f"Заточка: +{refine_level}")

    stats = []
    for key, label in _TRADE_STAT_LABELS_12_6_3.items():
        value = int(snapshot.get(key) or 0)
        if value:
            stats.append(f"• {label}: +{value}")
    if stats:
        lines.extend(["", "Характеристики:", *stats])

    runes = list(snapshot.get("runes") or [])
    if runes:
        lines.extend([
            "", "Вставлені руни:",
            *[f"• {row.get('rune_name') or row.get('rune_item_id')}" for row in runes],
        ])

    if include_quantity and snapshot.get("quantity") is not None:
        lines.append(f"Кількість: {int(snapshot.get('quantity') or 0)}")

    return lines

# ROM 12.6.4 PLAYER TRADE NAVIGATION LOCK AND ITEM CATEGORIES
from keyboards import main_kb
from systems.player_interaction_system import (
    get_active_player_trade,
    get_player_trade_category_counts,
    get_tradeable_inventory_for_trade_category,
)

PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4 = "🤝 Триває обмін"
PLAYER_TRADE_CATEGORY_PAGE_SIZE_12_6_4 = 8
_PLAYER_TRADE_CATEGORY_LABELS_12_6_4 = {
    "equipment": "⚔️ Спорядження",
    "potion": "🧪 Зілля",
    "material": "🪨 Матеріали",
    "rune": "💠 Руни",
}
_PLAYER_TRADE_ALLOWED_CALLBACK_PREFIXES_12_6_4 = (
    "pi:te:", "pi:teux:", "pi:tep:", "pi:tea:", "pi:tec:",
    "pi:trade:cancel:", "pi:req:accept:", "pi:req:decline:",
)


def player_trade_active_reply_kb_12_6_4():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton(PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4))
    return kb


def _trade_category_text_12_6_4(counts):
    return (
        "📦 <b>Категорії предметів</b>\n\nОберіть категорію:\n\n"
        f"⚔️ Спорядження: {int(counts.get('equipment', 0))}\n"
        f"🧪 Зілля: {int(counts.get('potion', 0))}\n"
        f"🪨 Матеріали: {int(counts.get('material', 0))}\n"
        f"💠 Руни: {int(counts.get('rune', 0))}"
    )


def _trade_category_kb_12_6_4(trade_id, counts):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton(
            f"⚔️ Спорядження ({int(counts.get('equipment', 0))})",
            callback_data=f"pi:tec:list:{trade_id}:equipment:0"),
        types.InlineKeyboardButton(
            f"🧪 Зілля ({int(counts.get('potion', 0))})",
            callback_data=f"pi:tec:list:{trade_id}:potion:0"),
    )
    kb.row(
        types.InlineKeyboardButton(
            f"🪨 Матеріали ({int(counts.get('material', 0))})",
            callback_data=f"pi:tec:list:{trade_id}:material:0"),
        types.InlineKeyboardButton(
            f"💠 Руни ({int(counts.get('rune', 0))})",
            callback_data=f"pi:tec:list:{trade_id}:rune:0"),
    )
    kb.row(types.InlineKeyboardButton(
        "✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb


def _trade_category_list_text_12_6_4(result):
    category = str(result.get("category") or "")
    total = int(result.get("total") or 0)
    page = int(result.get("page") or 0)
    page_size = int(result.get("page_size") or PLAYER_TRADE_CATEGORY_PAGE_SIZE_12_6_4)
    pages = max(1, (total + page_size - 1) // page_size)
    text = (
        f"{_PLAYER_TRADE_CATEGORY_LABELS_12_6_4.get(category, '📦 Предмети')}\n\n"
        f"Доступних позицій: {total}\nСторінка: {page + 1}/{pages}\n\n"
    )
    return text + ("Оберіть предмет:" if result.get("items") else "У цій категорії немає доступних предметів.")


def _trade_category_list_kb_12_6_4(result):
    trade_id = int(result["trade_id"])
    category = str(result["category"])
    page = int(result.get("page") or 0)
    kb = types.InlineKeyboardMarkup(row_width=1)
    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name_builder = globals().get("_trade_add_list_display_name_12_6_3a")
        name = name_builder(snapshot) if callable(name_builder) else str(
            snapshot.get("item_name") or snapshot.get("name") or f"Предмет #{snapshot.get('item_id')}"
        )
        remaining = int(item.get("available_quantity") or 0)
        suffix = "" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name + suffix,
            callback_data=(
                f"pi:tec:view:{trade_id}:{category}:"
                f"{int(item['inventory_id'])}:{page}"
            ),
        ))
    nav = []
    if result.get("has_previous"):
        nav.append(types.InlineKeyboardButton(
            "⬅️", callback_data=f"pi:tec:list:{trade_id}:{category}:{page-1}"))
    if result.get("has_next"):
        nav.append(types.InlineKeyboardButton(
            "➡️", callback_data=f"pi:tec:list:{trade_id}:{category}:{page+1}"))
    if nav:
        kb.row(*nav)
    kb.row(types.InlineKeyboardButton(
        "🔙 До категорій", callback_data=f"pi:tec:categories:{trade_id}"))
    kb.row(types.InlineKeyboardButton(
        "✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну", callback_data=f"pi:te:open:{trade_id}"))
    return kb


def _trade_category_preview_kb_12_6_4(preview, category, page):
    trade_id = int(preview["trade_id"])
    inventory_id = int(preview["inventory_id"])
    kb = types.InlineKeyboardMarkup(row_width=3)
    if preview.get("is_equipment"):
        kb.row(types.InlineKeyboardButton(
            "✅ Додати предмет",
            callback_data=f"pi:tec:addone:{trade_id}:{category}:{inventory_id}:{page}"))
    else:
        quantity = int(preview.get("offered_quantity") or 0)
        maximum = int(preview.get("maximum_quantity") or quantity)
        kb.row(
            types.InlineKeyboardButton(
                "➖", callback_data=f"pi:tec:set:{trade_id}:{category}:{inventory_id}:{max(0, quantity-1)}:{page}"),
            types.InlineKeyboardButton(
                f"x{quantity}", callback_data=f"pi:tec:view:{trade_id}:{category}:{inventory_id}:{page}"),
            types.InlineKeyboardButton(
                "➕", callback_data=f"pi:tec:set:{trade_id}:{category}:{inventory_id}:{min(maximum, quantity+1)}:{page}"),
        )
        if quantity < maximum:
            kb.row(types.InlineKeyboardButton(
                "📦 Додати все доступне",
                callback_data=f"pi:tec:all:{trade_id}:{category}:{inventory_id}:{page}"))
        kb.row(types.InlineKeyboardButton(
            "⌨️ Ввести кількість",
            callback_data=f"pi:tea:qinput:{trade_id}:{inventory_id}:{page}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До категорії",
        callback_data=f"pi:tec:list:{trade_id}:{category}:{page}"))
    kb.row(types.InlineKeyboardButton(
        "🔙 До категорій", callback_data=f"pi:tec:categories:{trade_id}"))
    return kb


def _trade_show_categories_12_6_4(bot, call, trade_id):
    result = get_player_trade_category_counts(trade_id, int(call.from_user.id))
    if not result.get("success"):
        _safe_answer(bot, call, "Обмін уже недоступний.", True)
        return
    counts = result.get("counts") or {}
    _safe_edit_message_text(
        bot, _trade_category_text_12_6_4(counts), call.message.chat.id,
        call.message.message_id, parse_mode="HTML",
        reply_markup=_trade_category_kb_12_6_4(trade_id, counts))


def _trade_show_category_list_12_6_4(bot, call, trade_id, category, page):
    result = get_tradeable_inventory_for_trade_category(
        trade_id, int(call.from_user.id), category,
        page=page, page_size=PLAYER_TRADE_CATEGORY_PAGE_SIZE_12_6_4)
    if not result.get("success"):
        _safe_answer(bot, call, "Категорія або обмін недоступні.", True)
        return
    _safe_edit_message_text(
        bot, _trade_category_list_text_12_6_4(result), call.message.chat.id,
        call.message.message_id, parse_mode="HTML",
        reply_markup=_trade_category_list_kb_12_6_4(result))


def _trade_is_amount_input_active_12_6_4(user_id):
    return int(user_id) in globals().get("TRADE_AMOUNT_INPUT_STATE_12_6_3", {})


def _trade_lock_allowed_callback_12_6_4(data):
    value = str(data or "")
    return value.startswith(_PLAYER_TRADE_ALLOWED_CALLBACK_PREFIXES_12_6_4)


def _trade_extract_update_actor_12_6_4(update):
    message = getattr(update, "message", None)
    callback = getattr(update, "callback_query", None)
    actor = getattr(message, "from_user", None) or getattr(callback, "from_user", None)
    return int(getattr(actor, "id", 0) or 0), message, callback


# ROM 12.6.5 PLAYER TRADE LOCK CONSOLIDATION AND STARTUP RECOVERY

def install_player_trade_navigation_lock_12_6_4(bot):
    """Install exactly one canonical active-trade navigation lock.

    The persistent `🤝 Триває обмін` ReplyKeyboard button is a strict no-op.
    Trade inline callbacks and manual amount input pass through. Other gameplay
    messages/callbacks are blocked with bounded feedback.
    """
    if getattr(bot, "_rom_trade_navigation_lock_12_6_5", False):
        return {"success": True, "installed": False}

    original = bot.process_new_updates
    notice_at = {}

    def notice_allowed(user_id):
        import time
        uid = int(user_id)
        now = time.monotonic()
        previous = float(notice_at.get(uid, -10**9))
        if now - previous < 10.0:
            return False
        notice_at[uid] = now
        return True

    def wrapped(updates):
        allowed = []
        notice_sent = set()

        for update in updates:
            user_id, message, callback = _trade_extract_update_actor_12_6_4(update)
            trade = get_active_player_trade(user_id) if user_id else None
            if not trade:
                allowed.append(update)
                continue

            if message is not None:
                text = str(getattr(message, "text", "") or "")

                # Strict no-op. Do not call Telegram API, refresh the editor,
                # mutate state, or touch a cooldown for this status button.
                if text == PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4:
                    continue

                if _trade_is_amount_input_active_12_6_4(user_id):
                    allowed.append(update)
                    continue

                if user_id not in notice_sent and notice_allowed(user_id):
                    notice_sent.add(user_id)
                    bot.send_message(
                        message.chat.id,
                        "🤝 Зараз триває обмін.\n\n"
                        "Завершіть або скасуйте поточний обмін, перш ніж "
                        "виконувати інші дії.",
                        reply_markup=player_trade_active_reply_kb_12_6_4(),
                    )
                continue

            if callback is not None:
                if _trade_lock_allowed_callback_12_6_4(
                    getattr(callback, "data", "")
                ):
                    allowed.append(update)
                elif user_id not in notice_sent and notice_allowed(user_id):
                    notice_sent.add(user_id)
                    try:
                        bot.answer_callback_query(
                            callback.id,
                            "Завершіть або скасуйте поточний обмін.",
                            show_alert=True,
                        )
                    except Exception:
                        pass
                continue

            allowed.append(update)

        if allowed:
            return original(allowed)
        return None

    bot.process_new_updates = wrapped
    bot._rom_trade_navigation_lock_12_6_4 = True
    bot._rom_trade_navigation_lock_12_6_5 = True
    return {"success": True, "installed": True}



def _register_trade_navigation_and_categories_12_6_4(bot):

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:categories:"))
    def trade_categories(call):
        _safe_answer(bot, call)
        try: trade_id = int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError): return
        _trade_show_categories_12_6_4(bot, call, trade_id)

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:list:"))
    def trade_category_list(call):
        _safe_answer(bot, call)
        try:
            _, _, _, trade_id, category, page = str(call.data).split(":")
            trade_id=int(trade_id); page=int(page)
        except (TypeError, ValueError): return
        _trade_show_category_list_12_6_4(bot, call, trade_id, category, page)

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:view:"))
    def trade_category_preview(call):
        _safe_answer(bot, call)
        try:
            _, _, _, trade_id, category, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        preview = get_trade_item_preview(trade_id, int(call.from_user.id), inventory_id)
        if not preview.get("success"):
            _safe_answer(bot, call, preview.get("message") or "Предмет недоступний.", True)
            return
        _safe_edit_message_text(
            bot, _trade_preview_text_12_6_2(preview), call.message.chat.id,
            call.message.message_id, parse_mode="HTML",
            reply_markup=_trade_category_preview_kb_12_6_4(preview, category, page))

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:addone:"))
    def trade_category_add_one(call):
        try:
            _, _, _, trade_id, category, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        result = set_player_trade_item_offer(
            trade_id, int(call.from_user.id), inventory_id, 1)
        if not result.get("success"):
            _safe_answer(bot, call, result.get("message") or "Не вдалося додати предмет.", True)
            return
        _safe_answer(bot, call, "Предмет додано.")
        _trade_show_category_list_12_6_4(bot, call, trade_id, category, page)

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:set:"))
    def trade_category_set(call):
        try:
            parts=str(call.data).split(":")
            trade_id=int(parts[3]); category=parts[4]; inventory_id=int(parts[5]); quantity=int(parts[6]); page=int(parts[7])
        except (IndexError, TypeError, ValueError): return
        existing = get_trade_offer_entry(trade_id, int(call.from_user.id), inventory_id)
        if quantity <= 0:
            result = remove_player_trade_item_offer(
                trade_id, int(call.from_user.id), inventory_id) if existing else {"success": True}
        else:
            result = set_player_trade_item_offer(
                trade_id, int(call.from_user.id), inventory_id, quantity)
        if not result.get("success"):
            _safe_answer(bot, call, result.get("message") or "Не вдалося змінити кількість.", True)
            return
        _safe_answer(bot, call, "Кількість оновлено.")
        preview = get_trade_item_preview(trade_id, int(call.from_user.id), inventory_id)
        if preview.get("success"):
            _safe_edit_message_text(
                bot, _trade_preview_text_12_6_2(preview), call.message.chat.id,
                call.message.message_id, parse_mode="HTML",
                reply_markup=_trade_category_preview_kb_12_6_4(preview, category, page))
        else:
            _trade_show_category_list_12_6_4(bot, call, trade_id, category, page)

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:tec:all:"))
    def trade_category_all(call):
        try:
            _, _, _, trade_id, category, inventory_id, page = str(call.data).split(":")
            trade_id=int(trade_id); inventory_id=int(inventory_id); page=int(page)
        except (TypeError, ValueError): return
        result = add_all_available_to_trade_offer(
            trade_id, int(call.from_user.id), inventory_id)
        if not result.get("success"):
            _safe_answer(bot, call, result.get("message") or "Не вдалося додати весь стек.", True)
            return
        _safe_answer(bot, call, "Увесь доступний стек додано.")
        _trade_show_category_list_12_6_4(bot, call, trade_id, category, page)

    @bot.callback_query_handler(func=lambda c: str(getattr(c, "data", "")).startswith("pi:trade:cancel:"))
    def trade_cancel_with_keyboard_restore(call):
        _safe_answer(bot, call)
        try: trade_id=int(str(call.data).rsplit(":", 1)[1])
        except (TypeError, ValueError): return
        result=cancel_player_trade(trade_id, int(call.from_user.id))
        if not result.get("success"):
            bot.send_message(call.message.chat.id, "ℹ️ Обмін уже неактивний.", reply_markup=main_kb())
            return
        globals().get("TRADE_AMOUNT_INPUT_STATE_12_6_3", {}).pop(int(call.from_user.id), None)
        own="❌ Обмін скасовано.\n\n✅ Персонаж знову доступний для інших дій."
        _safe_edit_message_text(bot, own, call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Повернення до основного меню.", reply_markup=main_kb())
        other=(int(result["recipient_user_id"]) if int(call.from_user.id)==int(result["initiator_user_id"]) else int(result["initiator_user_id"]))
        globals().get("TRADE_AMOUNT_INPUT_STATE_12_6_3", {}).pop(other, None)
        try:
            bot.send_message(other, "❌ Інший гравець скасував обмін.\n\n✅ Персонаж знову доступний для інших дій.", reply_markup=main_kb())
        except Exception:
            pass


# Final main trade keyboard override: item selection starts from categories.
def _trade_editor_kb(trade_id):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("➕ Додати предмет", callback_data=f"pi:tec:categories:{trade_id}"),
        types.InlineKeyboardButton("💰 Додати золото", callback_data=f"pi:tea:gold:{trade_id}"),
    )
    kb.row(types.InlineKeyboardButton("✏️ Моя пропозиція", callback_data=f"pi:teux:mine:{trade_id}"))
    kb.row(
        types.InlineKeyboardButton("🔄 Оновити", callback_data=f"pi:te:open:{trade_id}"),
        types.InlineKeyboardButton("❌ Скасувати обмін", callback_data=f"pi:trade:cancel:{trade_id}"),
    )
    return kb


_trade_navigation_base_register_12_6_4 = register_player_interaction_handlers

def register_player_interaction_handlers(bot):
    _register_trade_navigation_and_categories_12_6_4(bot)
    result = _trade_navigation_base_register_12_6_4(bot)
    install_player_trade_navigation_lock_12_6_4(bot)
    return result

# ROM 12.6.4a PLAYER TRADE IMMEDIATE KEYBOARD AND LOCK SPAM HOTFIX






# ROM 12.6.4b PLAYER TRADE CATEGORY PAGINATION LABELS

def _trade_category_list_kb_12_6_4(result):
    """Final categorized trade list keyboard with readable page navigation."""
    trade_id = int(result["trade_id"])
    category = str(result["category"])
    page = int(result.get("page") or 0)
    kb = types.InlineKeyboardMarkup(row_width=1)

    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name_builder = globals().get("_trade_add_list_display_name_12_6_3a")
        name = name_builder(snapshot) if callable(name_builder) else str(
            snapshot.get("item_name")
            or snapshot.get("name")
            or f"Предмет #{snapshot.get('item_id')}"
        )
        remaining = int(item.get("available_quantity") or 0)
        suffix = "" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name + suffix,
            callback_data=(
                f"pi:tec:view:{trade_id}:{category}:"
                f"{int(item['inventory_id'])}:{page}"
            ),
        ))

    # Keep the Auction House UX: one readable navigation button per row.
    if result.get("has_previous"):
        kb.row(types.InlineKeyboardButton(
            "⬅️ Попередні",
            callback_data=f"pi:tec:list:{trade_id}:{category}:{page-1}",
        ))
    if result.get("has_next"):
        kb.row(types.InlineKeyboardButton(
            "➡️ Наступні",
            callback_data=f"pi:tec:list:{trade_id}:{category}:{page+1}",
        ))

    kb.row(types.InlineKeyboardButton(
        "🔙 До категорій",
        callback_data=f"pi:tec:categories:{trade_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        "✏️ Моя пропозиція",
        callback_data=f"pi:teux:mine:{trade_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну",
        callback_data=f"pi:te:open:{trade_id}",
    ))
    return kb

# ROM 12.6.4c PLAYER TRADE CONTEXTUAL NAVIGATION CLEANUP

def _trade_category_list_kb_12_6_4(result):
    """Categorized add-list keyboard without unrelated My Offer navigation."""
    trade_id = int(result["trade_id"])
    category = str(result["category"])
    page = int(result.get("page") or 0)
    kb = types.InlineKeyboardMarkup(row_width=1)

    for item in result.get("items", []):
        snapshot = item.get("snapshot") or {}
        name_builder = globals().get("_trade_add_list_display_name_12_6_3a")
        name = name_builder(snapshot) if callable(name_builder) else str(
            snapshot.get("item_name")
            or snapshot.get("name")
            or f"Предмет #{snapshot.get('item_id')}"
        )
        remaining = int(item.get("available_quantity") or 0)
        suffix = "" if item.get("is_equipment") else f" (можна додати {remaining})"
        kb.add(types.InlineKeyboardButton(
            name + suffix,
            callback_data=(
                f"pi:tec:view:{trade_id}:{category}:"
                f"{int(item['inventory_id'])}:{page}"
            ),
        ))

    if result.get("has_previous"):
        kb.row(types.InlineKeyboardButton(
            "⬅️ Попередні",
            callback_data=f"pi:tec:list:{trade_id}:{category}:{page-1}",
        ))
    if result.get("has_next"):
        kb.row(types.InlineKeyboardButton(
            "➡️ Наступні",
            callback_data=f"pi:tec:list:{trade_id}:{category}:{page+1}",
        ))

    kb.row(types.InlineKeyboardButton(
        "🔙 До категорій",
        callback_data=f"pi:tec:categories:{trade_id}",
    ))
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну",
        callback_data=f"pi:te:open:{trade_id}",
    ))
    return kb


def _trade_ux_mine_kb(state):
    """My Offer keyboard without Add Item when the offer is empty."""
    trade_id = int(state["trade"]["id"])
    kb = types.InlineKeyboardMarkup(row_width=1)
    for offer in state.get("own_offers", []):
        if offer.get("asset_type") == "gold":
            kb.add(types.InlineKeyboardButton(
                f"💰 Золото: {float(offer.get('gold_amount') or 0):.2f}",
                callback_data=f"pi:teux:gold:{trade_id}",
            ))
        else:
            kb.add(types.InlineKeyboardButton(
                f"{_trade_ux_offer_name(offer)} x{int(offer.get('quantity') or 1)}",
                callback_data=(
                    f"pi:teux:edit:{trade_id}:"
                    f"{int(offer['inventory_id'])}"
                ),
            ))

    # Empty offer intentionally has no Add Item shortcut. Item addition starts
    # only from the main trade screen, which keeps navigation unambiguous.
    kb.row(types.InlineKeyboardButton(
        "🔙 До обміну",
        callback_data=f"pi:te:open:{trade_id}",
    ))
    return kb

# ROM 12.6.4d PLAYER TRADE AMOUNT CANCEL AND LOCK RECOVERY







# ROM 12.6.4e PLAYER TRADE REOPEN DEDUPLICATION HOTFIX









# ROM 12.6.4f PLAYER TRADE REOPEN DISTINCT UPDATE FIX




# ROM 12.6.4g PLAYER TRADE STATUS BUTTON STUB







# ROM 12.6.4h PLAYER TRADE STATUS BUTTON NOOP


