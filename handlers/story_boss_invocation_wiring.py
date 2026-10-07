"""Live Telegram wiring for the pure story-boss invocation adapter.

The module deliberately delegates forced invocation to the already registered canonical
`call_active_story_boss` message handler. It does not create a second combat pipeline.
"""
from __future__ import annotations
import inspect
from types import SimpleNamespace
from telebot import types
import db
from systems.story_boss_invocation_adapter import (
    HELP_CALLBACK,
    INVOKE_CALLBACK,
    RETURN_CALLBACK,
    StoryBossAction,
    build_story_boss_look_around_presentation,
    parse_story_boss_callback,
    story_boss_help_text,
)
from systems.story_quest_boss_call_system import get_active_story_boss_call

_REGISTERED_BOTS: set[int] = set()


def _player_stats(user_id: int):
    """Return canonical primary stats without assuming a mapping representation.

    `db.get_player_stats` currently returns the six-value tuple
    `(STR, DEX, INT, WIS, STA, level)`. Older tests and integrations may supply
    mappings or row-like objects, so the adapter preserves the value unchanged.
    Story-boss presentation does not derive location from this value.
    """
    getter = getattr(db, "get_player_stats", None)
    return getter(user_id) if callable(getter) else None


def _location_id(user_id: int, stats=None) -> str:
    """Resolve location through the canonical location API with safe fallbacks.

    Location is account/runtime state and is not part of the primary-stat tuple.
    The mapping/attribute fallbacks keep compatibility with isolated tests only;
    production uses `db.get_current_location` as the authoritative source.
    """
    getter = getattr(db, "get_current_location", None)
    if callable(getter):
        location = getter(user_id)
        if location:
            return str(location)
    for name in ("location_id", "current_location", "location"):
        if isinstance(stats, dict) and stats.get(name):
            return str(stats[name])
        value = getattr(stats, name, None)
        if value:
            return str(value)
    return ""


def _invoke_supported(function, values: dict):
    signature = inspect.signature(function)
    positional = []
    keyword = {}
    for name, parameter in signature.parameters.items():
        if name not in values:
            if parameter.default is inspect.Parameter.empty and parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
                raise RuntimeError(f"unsupported required parameter for {function.__name__}: {name}")
            continue
        if parameter.kind is parameter.POSITIONAL_ONLY:
            positional.append(values[name])
        elif parameter.kind not in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            keyword[name] = values[name]
    return function(*positional, **keyword)


def _active_call(user_id: int, location_id: str):
    values = {"connection": db.conn, "conn": db.conn, "user_id": user_id, "location_id": location_id, "current_location_id": location_id}
    return _invoke_supported(get_active_story_boss_call, values)


def _value(obj, *names, default=None):
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _inline_markup(rows):
    markup = types.InlineKeyboardMarkup()
    for row in rows:
        markup.row(*(types.InlineKeyboardButton(text, callback_data=data) for text, data in row))
    return markup


def _presentation_for_user(user_id: int):
    stats = _player_stats(user_id)
    location_id = _location_id(user_id, stats)
    call = _active_call(user_id, location_id)
    # Eligibility denials are non-empty dictionaries. Render only the explicit
    # canonical allow contract; all missing/false/non-boolean values fail closed.
    if not call or _value(call, "allowed", default=False) is not True:
        return None
    from systems.story_boss_invocation_adapter import StoryBossInvocationState
    current = int(_value(call, "progress_current", "current", "progress", default=0) or 0)
    target = int(_value(call, "progress_target", "target", "target_quantity", default=1) or 1)
    quest_number = int(_value(call, "quest_number", "number", default=49) or 49)
    status = str(_value(call, "quest_status", "status", default="ACTIVE") or "ACTIVE")
    state = StoryBossInvocationState(
        quest_number=quest_number,
        quest_status=status,
        progress_current=current,
        progress_target=target,
        expected_location_id=str(_value(call, "location_id", "expected_location_id", default="start_path") or "start_path"),
        current_location_id=location_id,
        has_active_encounter=False,
        has_active_travel=False,
        is_busy=False,
    )
    return build_story_boss_look_around_presentation(state)


def send_story_boss_look_around_if_present(bot, message) -> bool:
    presentation = _presentation_for_user(message.from_user.id)
    if presentation is None:
        return False
    bot.send_message(message.chat.id, presentation.text_suffix, reply_markup=_inline_markup(presentation.rows))
    return True


def _canonical_call_handler(bot):
    matches = [item.get("function") for item in getattr(bot, "message_handlers", ()) if getattr(item.get("function"), "__name__", "") == "call_active_story_boss"]
    if len(matches) != 1:
        raise RuntimeError(f"canonical call_active_story_boss handler count: {len(matches)}")
    return matches[0]


def _delegate_invoke(bot, call):
    """Delegate through the canonical message handler with callback-user identity.

    Telegram callback messages were authored by the bot, so
    `call.message.from_user` is not the player who pressed the inline button.
    The canonical combat handler reads `message.from_user.id`; provide an
    adapter carrying `call.from_user` while preserving the source chat.
    """
    handler = _canonical_call_handler(bot)
    source_message = call.message
    player_message = SimpleNamespace(
        from_user=call.from_user,
        chat=source_message.chat,
        text=getattr(source_message, "text", None),
        message_id=getattr(source_message, "message_id", None),
        date=getattr(source_message, "date", None),
        content_type=getattr(source_message, "content_type", "text"),
    )
    # The canonical owner revalidates quest, location, encounter and retry eligibility.
    handler(player_message)


def _active_story_boss_callback_call(user_id: int, expected_quest_number: int):
    """Return the expected production BOSS quest only while its lifecycle is ACTIVE.

    Old Telegram callback buttons outlive the message that created them. Re-read
    current quest state before any HELP/RETURN/INVOKE branch instead of trusting
    the stale payload or current button visibility. ACTIVE 1/1 remains valid for
    report help, while COMPLETED, SKIPPED and AVAILABLE fail closed.
    """
    stats = _player_stats(user_id)
    location_id = _location_id(user_id, stats)
    call = _active_call(user_id, location_id)
    if not call:
        return None
    quest_number = int(_value(call, "quest_number", "number", default=0) or 0)
    quest_status = str(_value(call, "quest_status", "status", default="") or "").upper()
    if quest_number != int(expected_quest_number) or quest_status != "ACTIVE":
        return None
    return call


def register_story_boss_invocation_callbacks(bot) -> None:
    marker = id(bot)
    if marker in _REGISTERED_BOTS:
        return
    _REGISTERED_BOTS.add(marker)

    @bot.callback_query_handler(func=lambda call: str(getattr(call, "data", "")).startswith("sqboss:v1:"))
    def story_boss_invocation_callback(call):
        parsed = parse_story_boss_callback(call.data)
        if parsed is None:
            bot.answer_callback_query(call.id, "Ця дія більше недоступна.", show_alert=True)
            return
        action, quest_number = parsed
        if quest_number not in (49, 99):
            bot.answer_callback_query(call.id, "Ця дія більше недоступна.", show_alert=True)
            return
        active_call = _active_story_boss_callback_call(call.from_user.id, quest_number)
        if active_call is None:
            bot.answer_callback_query(call.id, "Ця сюжетна дія більше неактуальна.", show_alert=True)
            return
        if action is StoryBossAction.HELP:
            current = int(_value(active_call, "progress_current", "current", "progress", default=0) or 0)
            target = int(_value(active_call, "progress_target", "target", "target_quantity", default=1) or 1)
            bot.answer_callback_query(call.id)
            if current >= target:
                boss_name = "Ватажка" if quest_number == 49 else "Короля Гоблінів"
                bot.send_message(call.message.chat.id, f"✅ {boss_name} вже переможено. Повернися до Міста → 📜 Гільдія Найманців → ⚔️ Голова Найманців і доповідь про перемогу.")
            else:
                bot.send_message(call.message.chat.id, story_boss_help_text(quest_number))
            return
        if action is StoryBossAction.RETURN:
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "🧭 Повернися до Міста → 📜 Гільдія Найманців → ⚔️ Голова Найманців.")
            return
        presentation = _presentation_for_user(call.from_user.id)
        expected_invoke = f"sqboss:v1:invoke:{quest_number}"
        if presentation is None or not any(data == expected_invoke for row in presentation.rows for _, data in row):
            bot.answer_callback_query(call.id, "Виклик сюжетного боса зараз недоступний.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        _delegate_invoke(bot, call)
