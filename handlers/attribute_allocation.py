#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram UI adapter for the canonical Attribute Allocation domain service."""
from __future__ import annotations

from threading import RLock
from telebot import types

from systems.attribute_allocation_system import (
    AttributeAllocationError,
    InsufficientAttributePointsError,
    InvalidAllocationError,
    StaleAttributeStateError,
    allocate_attribute_points,
    get_attribute_point_state,
)

ATTRIBUTE_ORDER = ("strength", "dexterity", "intelligence", "wisdom", "stamina")
ATTRIBUTE_LABELS = {
    "strength": "Сила",
    "dexterity": "Спритність",
    "intelligence": "Інтелект",
    "wisdom": "Мудрість",
    "stamina": "Витривалість",
}
ATTRIBUTE_ALLOCATION_STATE: dict[int, dict] = {}
_STATE_LOCK = RLock()
_REGISTERED_BOTS: set[int] = set()


def _empty_pending() -> dict[str, int]:
    return {name: 0 for name in ATTRIBUTE_ORDER}


def _new_draft(user_id: int) -> dict:
    state = get_attribute_point_state(user_id)
    return {
        "expected_free_attribute_points": state["free_attribute_points"],
        "pending": _empty_pending(),
    }


def _get_draft(user_id: int, *, refresh: bool = False) -> dict:
    with _STATE_LOCK:
        if refresh or user_id not in ATTRIBUTE_ALLOCATION_STATE:
            ATTRIBUTE_ALLOCATION_STATE[user_id] = _new_draft(user_id)
        return ATTRIBUTE_ALLOCATION_STATE[user_id]


def _clear_draft(user_id: int) -> None:
    with _STATE_LOCK:
        ATTRIBUTE_ALLOCATION_STATE.pop(user_id, None)


def build_attribute_allocation_text(user_id: int, draft: dict | None = None) -> str:
    state = get_attribute_point_state(user_id)
    draft = draft or _get_draft(user_id)
    pending = draft["pending"]
    pending_total = sum(pending.values())
    remaining = max(0, draft["expected_free_attribute_points"] - pending_total)
    lines = [
        "⭐ Розподіл характеристик",
        "",
        f"Вільні очки: {state['free_attribute_points']}",
        f"Заплановано: {pending_total}",
        f"Залишиться після підтвердження: {remaining}",
        "",
    ]
    for name in ATTRIBUTE_ORDER:
        allocated_key = f"allocated_{name}"
        lines.append(
            f"{ATTRIBUTE_LABELS[name]}: розподілено {state[allocated_key]}"
            f" | додати +{pending[name]}"
        )
    lines.extend((
        "",
        "Зміни застосуються атомарно лише після натискання «Підтвердити».",
    ))
    return "\n".join(lines)


def attribute_allocation_kb(user_id: int, navigation_kb_factory, draft: dict | None = None):
    draft = draft or _get_draft(user_id)
    pending = draft["pending"]
    pending_total = sum(pending.values())
    available = draft["expected_free_attribute_points"]
    kb = types.InlineKeyboardMarkup(row_width=3)
    for name in ATTRIBUTE_ORDER:
        kb.row(
            types.InlineKeyboardButton("➖", callback_data=f"attr:minus:{name}"),
            types.InlineKeyboardButton(
                f"{ATTRIBUTE_LABELS[name]} +{pending[name]}",
                callback_data="attr:noop",
            ),
            types.InlineKeyboardButton("➕", callback_data=f"attr:plus:{name}"),
        )
    if pending_total > 0:
        kb.row(
            types.InlineKeyboardButton("✅ Підтвердити", callback_data="attr:confirm"),
            types.InlineKeyboardButton("❌ Скасувати", callback_data="attr:cancel"),
        )
    else:
        kb.row(types.InlineKeyboardButton("❌ Скасувати", callback_data="attr:cancel"))
    kb.row(types.InlineKeyboardButton("🔙 Назад", callback_data="attr:back"))
    return kb


def _render(bot, call, navigation_kb_factory, *, refresh=False):
    user_id = call.from_user.id
    draft = _get_draft(user_id, refresh=refresh)
    text = build_attribute_allocation_text(user_id, draft)
    markup = attribute_allocation_kb(user_id, navigation_kb_factory, draft)
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)


def register_attribute_allocation_handlers(bot, navigation_kb_factory, character_text_factory) -> None:
    bot_key = id(bot)
    if bot_key in _REGISTERED_BOTS:
        return
    _REGISTERED_BOTS.add(bot_key)

    @bot.callback_query_handler(func=lambda call: call.data == "profile_attributes")
    def open_attribute_allocation(call):
        bot.answer_callback_query(call.id)
        _render(bot, call, navigation_kb_factory, refresh=True)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("attr:"))
    def attribute_allocation_callback(call):
        user_id = call.from_user.id
        parts = str(call.data).split(":")
        action = parts[1] if len(parts) > 1 else ""

        if action == "noop":
            bot.answer_callback_query(call.id)
            return
        if action == "cancel":
            _clear_draft(user_id)
            bot.answer_callback_query(call.id, "Чернетку скасовано")
            _render(bot, call, navigation_kb_factory, refresh=True)
            return
        if action == "back":
            _clear_draft(user_id)
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                character_text_factory(user_id),
                reply_markup=navigation_kb_factory(active_tab="character"),
            )
            return


        draft = _get_draft(user_id)
        if action in {"plus", "minus"} and len(parts) == 3:
            attribute = parts[2]
            if attribute not in ATTRIBUTE_ORDER:
                bot.answer_callback_query(call.id, "Невідома характеристика", show_alert=True)
                return
            pending = draft["pending"]
            if action == "plus":
                if sum(pending.values()) >= draft["expected_free_attribute_points"]:
                    bot.answer_callback_query(call.id, "Немає вільних очок", show_alert=True)
                    return
                pending[attribute] += 1
            elif pending[attribute] > 0:
                pending[attribute] -= 1
            bot.answer_callback_query(call.id)
            _render(bot, call, navigation_kb_factory)
            return

        if action == "confirm":
            allocation = {name: value for name, value in draft["pending"].items() if value > 0}
            if not allocation:
                bot.answer_callback_query(call.id, "Немає запланованих змін", show_alert=True)
                return
            try:
                result = allocate_attribute_points(
                    user_id,
                    allocation,
                    expected_free_attribute_points=draft["expected_free_attribute_points"],
                )
            except StaleAttributeStateError:
                _clear_draft(user_id)
                bot.answer_callback_query(
                    call.id,
                    "Баланс очок змінився. Меню оновлено.",
                    show_alert=True,
                )
                _render(bot, call, navigation_kb_factory, refresh=True)
                return
            except InsufficientAttributePointsError:
                _clear_draft(user_id)
                bot.answer_callback_query(call.id, "Недостатньо вільних очок", show_alert=True)
                _render(bot, call, navigation_kb_factory, refresh=True)
                return
            except (InvalidAllocationError, AttributeAllocationError):
                _clear_draft(user_id)
                bot.answer_callback_query(call.id, "Розподіл не застосовано", show_alert=True)
                _render(bot, call, navigation_kb_factory, refresh=True)
                return
            _clear_draft(user_id)
            bot.answer_callback_query(
                call.id,
                f"Розподілено очок: {result['spent']}",
                show_alert=True,
            )
            _render(bot, call, navigation_kb_factory, refresh=True)
            return

        bot.answer_callback_query(call.id, "Невідома дія", show_alert=True)
