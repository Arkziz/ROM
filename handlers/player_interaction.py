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
        cancel_kb = types.InlineKeyboardMarkup(row_width=1)
        cancel_kb.add(types.InlineKeyboardButton("❌ Скасувати обмін", callback_data=f"pi:trade:cancel:{trade_id}"))
        text = "✅ Запрошення прийнято.\n\nСесію обміну створено на 10 хвилин. Редактор пропозиції буде додано наступним етапом."
        _safe_edit_message_text(bot, text, call.message.chat.id, call.message.message_id, reply_markup=cancel_kb)
        try:
            bot.send_message(int(result["initiator_user_id"]), text, reply_markup=cancel_kb)
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

