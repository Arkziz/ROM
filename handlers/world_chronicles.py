# -*- coding: utf-8 -*-
"""Telegram UI for ROM World Chronicles."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from telebot import types

from systems.world_chronicle_system import (
    WORLD_CHRONICLE_PAGE_SIZE,
    get_world_chronicle_page,
)

WORLD_CHRONICLES_BUTTON = "📜 Хроніки світу"
WORLD_CHRONICLES_CALLBACK_PREFIX = "wc:"


def _format_world_chronicle_time(value):
    raw = str(value or "").strip()
    if not raw:
        return "час невідомий"
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        return raw[:16].replace("T", " ")


def _world_chronicle_event_text(row):
    event_type = str(row.get("event_type") or "")
    actor_name = str(row.get("actor_name_snapshot") or "Мандрівник")
    subject_name = str(row.get("subject_name_snapshot") or "")
    try:
        metadata = json.loads(row.get("metadata_json") or "{}")
    except Exception:
        metadata = {}

    if event_type == "player_joined":
        body = f"🌟 У світі з'явився новий мандрівник: {actor_name}."
    elif event_type == "player_level_up":
        body = f"🏆 {actor_name} досяг {int(metadata.get('level') or 1)} рівня."
    elif event_type == "equipment_max_refine":
        level = int(metadata.get("level") or 0)
        body = f"⚒️ {actor_name} покращив предмет «{subject_name or 'Спорядження'}» до максимального рівня +{level}."
    elif event_type == "location_boss_defeated":
        body = f"👑 {actor_name} переміг боса «{subject_name or 'Бос'}»."
    else:
        body = "📜 У світі сталася важлива подія."

    return f"{body}\n🕒 {_format_world_chronicle_time(row.get('created_at'))}"


def build_world_chronicles_text(data):
    lines = ["📜 ХРОНІКИ СВІТУ", ""]
    items = list(data.get("items") or [])
    if not items:
        lines.append("Важливих подій поки немає.")
    else:
        for item in items:
            lines.extend([_world_chronicle_event_text(item), ""])
    lines.append(f"Сторінка {int(data.get('page') or 0) + 1}")
    return "\n".join(lines).strip()


def world_chronicles_kb(data):
    keyboard = types.InlineKeyboardMarkup()
    navigation = []
    page = int(data.get("page") or 0)
    if data.get("has_previous"):
        navigation.append(types.InlineKeyboardButton("◀️", callback_data=f"wc:page:{page - 1}"))
    if data.get("has_next"):
        navigation.append(types.InlineKeyboardButton("▶️", callback_data=f"wc:page:{page + 1}"))
    if navigation:
        keyboard.row(*navigation)
    keyboard.row(types.InlineKeyboardButton("🔄 Оновити", callback_data="wc:refresh"))
    keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="wc:back"))
    return keyboard


def _show_world_chronicles(bot, chat_id, page=0, message_id=None):
    data = get_world_chronicle_page(page=page, page_size=WORLD_CHRONICLE_PAGE_SIZE)
    text = build_world_chronicles_text(data)
    keyboard = world_chronicles_kb(data)
    if message_id is None:
        bot.send_message(chat_id, text, reply_markup=keyboard)
    else:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)


def register_world_chronicle_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == WORLD_CHRONICLES_BUTTON)
    def open_world_chronicles(message):
        _show_world_chronicles(bot, message.chat.id, page=0)

    @bot.callback_query_handler(func=lambda call: str(call.data or "").startswith(WORLD_CHRONICLES_CALLBACK_PREFIX))
    def world_chronicles_callback(call):
        data = str(call.data or "")
        if data == "wc:back":
            from handlers.city import (
                account_menu_kb_17_30_1_4,
                build_account_menu_text_17_30_1_4,
            )
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                build_account_menu_text_17_30_1_4(call.from_user.id),
                reply_markup=account_menu_kb_17_30_1_4(),
            )
            return

        if data == "wc:refresh":
            page = 0
        elif data.startswith("wc:page:"):
            try:
                page = max(0, int(data.rsplit(":", 1)[1]))
            except Exception:
                page = 0
        else:
            bot.answer_callback_query(call.id)
            return

        _show_world_chronicles(
            bot,
            call.message.chat.id,
            page=page,
            message_id=call.message.message_id,
        )
        bot.answer_callback_query(call.id)
