# -*- coding: utf-8 -*-
"""Fail-closed external URL navigation for ROM Stage 18.5.1."""
from telebot import types

from config import get_external_links_config

EXTERNAL_LINKS_BUTTON = "🔗 Корисні посилання"
EXTERNAL_LINKS_CLOSE_CALLBACK = "links:close"


def _external_links_text(has_links):
    if has_links:
        return "🔗 Корисні посилання\n\nОберіть потрібний ресурс:"
    return (
        "🔗 Корисні посилання\n\n"
        "Наразі доступні посилання ще не налаштовані."
    )


def _external_links_kb(links=None):
    links = dict(get_external_links_config() if links is None else links)
    keyboard = types.InlineKeyboardMarkup()
    if links.get("game_chat"):
        keyboard.row(types.InlineKeyboardButton("💬 Чат гри", url=links["game_chat"]))
    if links.get("news_channel"):
        keyboard.row(types.InlineKeyboardButton("📰 Канал новин", url=links["news_channel"]))
    if links.get("support"):
        keyboard.row(types.InlineKeyboardButton("❤️ Підтримати проєкт", url=links["support"]))
    keyboard.row(types.InlineKeyboardButton("❌ Закрити", callback_data=EXTERNAL_LINKS_CLOSE_CALLBACK))
    return keyboard


def _return_account_menu(bot, chat_id, user_id, message_id):
    from handlers.city import build_account_menu_text_17_30_1_4, account_menu_kb_17_30_1_4
    try:
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)
    except Exception:
        pass
    bot.send_message(
        chat_id,
        build_account_menu_text_17_30_1_4(user_id),
        reply_markup=account_menu_kb_17_30_1_4(),
    )


def register_external_links_handlers(bot):
    @bot.message_handler(
        func=lambda message: str(getattr(message, "text", "") or "") == EXTERNAL_LINKS_BUTTON
    )
    def open_external_links(message):
        links = get_external_links_config()
        bot.send_message(
            message.chat.id,
            _external_links_text(any(links.values())),
            reply_markup=_external_links_kb(links),
        )

    @bot.callback_query_handler(
        func=lambda call: str(getattr(call, "data", "") or "") == EXTERNAL_LINKS_CLOSE_CALLBACK
    )
    def close_external_links(call):
        bot.answer_callback_query(call.id)
        _return_account_menu(
            bot,
            call.message.chat.id,
            call.from_user.id,
            call.message.message_id,
        )
