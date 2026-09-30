"""Pure UI foundation for the ROM story-quest journal.

This module intentionally registers no Telegram handlers. Stage 19.10 will wire
its canonical builders into Profile after a focused production-route mutation.
Keeping rendering pure makes empty, active and history states testable without
starting the bot or touching production game.db.
"""
from __future__ import annotations
from systems.story_quest_location_presentation import resolve_story_quest_location_name

from dataclasses import dataclass
from data.story_quest_definitions import QuestType
from typing import Iterable, Mapping, Optional, Sequence
from systems.story_quest_player_level import resolve_story_quest_player_level
from handlers.story_quest_hierarchy_ui import (
    ROOT_CALLBACK as STORY_HIERARCHY_ROOT_CALLBACK,
    build_section_index,
    build_section_quests,
    build_story_index,
    parse_hierarchy_callback,
    section_callback_for_quest,
)

STORY_QUEST_BUTTON_TEXT = "📜 Квести"
STORY_QUEST_CALLBACK_PREFIX = "story_quest:"
STORY_QUEST_PAGE_SIZE = 10
STATUS_LABELS = {
    "LOCKED": "🔒 Недоступний",
    "AVAILABLE": "✨ Доступний",
    "ACTIVE": "📖 Активний",
    "COMPLETED": "✅ Виконаний",
    "SKIPPED": "⏭️ Пропущений",
}


class StoryQuestUiError(ValueError):
    """A callback or UI snapshot violates the story-journal contract."""


@dataclass(frozen=True)
class StoryQuestCallback:
    """Validated callback payload decoded from the story-quest namespace."""

    action: str
    value: str = ""


def build_story_quest_callback(action: str, value: str = "") -> str:
    """Build a compact namespaced callback accepted by the future handler."""
    action_key = str(action or "").strip().lower()
    value_key = str(value or "").strip()
    if not action_key or ":" in action_key or ":" in value_key:
        raise StoryQuestUiError("invalid story quest callback component")
    payload = f"{STORY_QUEST_CALLBACK_PREFIX}{action_key}"
    if value_key:
        payload += f":{value_key}"
    if len(payload.encode("utf-8")) > 64:
        raise StoryQuestUiError("story quest callback exceeds Telegram limit")
    return payload


def parse_story_quest_callback(payload: str) -> StoryQuestCallback:
    """Fail closed for callbacks outside the canonical namespace."""
    raw = str(payload or "")
    if not raw.startswith(STORY_QUEST_CALLBACK_PREFIX):
        raise StoryQuestUiError("foreign callback namespace")
    parts = raw[len(STORY_QUEST_CALLBACK_PREFIX):].split(":")
    if not parts or not parts[0] or len(parts) > 2:
        raise StoryQuestUiError("invalid story quest callback")
    return StoryQuestCallback(parts[0], parts[1] if len(parts) == 2 else "")


def _button(text: str, callback_data: str) -> dict:
    """Return a Telegram-library-neutral inline button descriptor."""
    return {"text": str(text), "callback_data": str(callback_data)}


def build_story_quest_journal_keyboard(
    *, page: int, has_previous: bool, has_next: bool,
) -> list[list[dict]]:
    """Build deterministic journal navigation with canonical Profile return."""
    current = max(0, int(page))
    rows = []
    navigation = []
    if has_previous:
        navigation.append(_button("⬅️ Назад", build_story_quest_callback("page", str(current - 1))))
    if has_next:
        navigation.append(_button("➡️ Далі", build_story_quest_callback("page", str(current + 1))))
    if navigation:
        rows.append(navigation)
    rows.append([_button("🔄 Оновити", build_story_quest_callback("refresh", str(current)))])
    rows.append([_button("🔙 До профілю", build_story_quest_callback("profile"))])
    return rows


def build_story_quest_detail_keyboard(
    *, quest_id: str, status: str, page: int = 0,
) -> list[list[dict]]:
    """Expose only actions valid for the supplied materialized/derived status."""
    quest_key = str(quest_id or "").strip()
    if not quest_key:
        raise StoryQuestUiError("quest_id is required")
    rows = []
    # The route is already visible in the detail text. Keep the journal compact
    # and navigation-only without a redundant callback button.
    rows.append([_button("🔙 До журналу", build_story_quest_callback("page", str(max(0, int(page)))))])
    return rows


def _status_label(status: str) -> str:
    try:
        return STATUS_LABELS[str(status)]
    except KeyError as error:
        raise StoryQuestUiError(f"unknown story quest status: {status}") from error


def render_story_quest_journal(
    items: Sequence[Mapping], *, page: int = 0, page_size: int = STORY_QUEST_PAGE_SIZE,
) -> dict:
    """Render a paginated, UI-neutral journal snapshot.

    Items are expected to come from the lifecycle view layer. The formatter does
    not query SQLite, infer NPC routes, or duplicate lifecycle decisions.
    """
    size = max(1, min(STORY_QUEST_PAGE_SIZE, int(page_size)))
    ordered = sorted(items, key=lambda item: (int(item.get("number", 0)), str(item.get("quest_id", ""))))
    max_page = max(0, (len(ordered) - 1) // size) if ordered else 0
    current = min(max(0, int(page)), max_page)
    visible = ordered[current * size:(current + 1) * size]
    if not visible:
        text = "📜 Сюжетні квести\n\nЖурнал поки порожній."
    else:
        lines = ["📜 Сюжетні квести", ""]
        for item in visible:
            number = int(item.get("number", 0))
            title = str(item.get("title") or "Без назви")
            status = str(item.get("status") or "LOCKED")
            lines.append(f"{number}. {title}")
            lines.append(f"   {_status_label(status)}")
            if status == "ACTIVE":
                progress = int(item.get("quest_item_quantity", 0) or item.get("progress", 0))
                target = int(item.get("target_quantity", 1))
                lines.append(f"   Прогрес: {min(progress, target)}/{target}")
        lines += ["", f"Сторінка {current + 1}/{max_page + 1}"]
        text = "\n".join(lines)
    quest_rows = [
        [_button(
            f"{STATUS_LABELS.get(str(item.get('status') or 'LOCKED'),'❓')} {int(item.get('number',0))}. {str(item.get('title') or 'Без назви')}",
            build_story_quest_callback("detail", str(item.get("quest_id") or "")),
        )]
        for item in visible
    ]
    return {
        "text": text,
        "page": current,
        "page_size": size,
        "total": len(ordered),
        "has_previous": current > 0,
        "has_next": current < max_page,
        "keyboard": quest_rows + build_story_quest_journal_keyboard(
            page=current, has_previous=current > 0, has_next=current < max_page,
        ),
        "visible_quest_ids": [str(item.get("quest_id", "")) for item in visible],
    }


def render_story_quest_detail(item: Mapping, *, page: int = 0) -> dict:
    """Render one quest using only canonical lifecycle snapshot fields."""
    quest_id = str(item.get("quest_id") or "").strip()
    if not quest_id:
        raise StoryQuestUiError("quest_id is required")
    status = str(item.get("status") or "LOCKED")
    progress = int(item.get("quest_item_quantity", 0) or item.get("progress", 0))
    target = int(item.get("target_quantity", 1))
    lines = [
        f"📜 {int(item.get('number', 0))}. {str(item.get('title') or 'Без назви')}",
        "",
        _status_label(status),
        f"Прогрес: {min(progress, target)}/{target}",
    ]
    return {
        "text": "\n".join(lines),
        "keyboard": build_story_quest_detail_keyboard(
            quest_id=quest_id, status=status, page=page,
        ),
    }



def _inline_markup(rows):
    """Convert pure descriptors to telebot markup only at the delivery boundary."""
    from telebot import types

    markup = types.InlineKeyboardMarkup()
    for row in rows:
        markup.row(*[
            types.InlineKeyboardButton(
                text=button["text"], callback_data=button["callback_data"]
            )
            for button in row
        ])
    return markup


def _send_empty_story_journal(bot, chat_id):
    """Show the safe empty journal until reviewed production content exists."""
    snapshot = render_story_quest_journal([])
    bot.send_message(
        chat_id,
        snapshot["text"],
        reply_markup=_inline_markup(snapshot["keyboard"]),
    )



def _edit_story_journal_safely(bot, *, chat_id, message_id, text, reply_markup):
    """Edit the journal while treating Telegram's identical-content 400 as success.

    Refresh may legitimately reproduce the same text and keyboard. Telegram
    rejects that no-op edit with HTTP 400, but the journal is already current.
    Only that exact condition is suppressed; every unrelated API error remains
    visible to the polling/recovery layer.
    """
    from telebot.apihelper import ApiTelegramException

    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            reply_markup=reply_markup,
        )
        return True
    except ApiTelegramException as error:
        description = str(error).casefold()
        if "message is not modified" in description:
            return False
        raise

def build_production_story_quest_detail(connection, *, user_id: int, quest_id: str, player_level: int, page: int = 0) -> dict:
    """Render one canonical definition plus current lifecycle state.

    Acceptance remains NPC-owned. The journal only explains the objective,
    route, progress, reward, and unlock prerequisites.
    """
    import db
    from data.story_quest_content import STORY_QUEST_REGISTRY
    from data.story_quest_npcs import resolve_story_quest_navigation
    from systems.story_quest_system import get_story_quest_view
    try:
        quest = STORY_QUEST_REGISTRY[str(quest_id)]
    except KeyError as error:
        raise StoryQuestUiError(f"unknown production story quest: {quest_id}") from error
    view = get_story_quest_view(connection, user_id=int(user_id), quest=quest, player_level=int(player_level))
    navigation = quest.navigation
    status = str(view["status"])
    progress = max(int(view.get("progress",0)), int(view.get("quest_item_quantity",0)))
    lines = [f"📜 {quest.number}. {quest.title}", "", f"Статус: {_status_label(status)}", "", "📖 Опис:", quest.description, "", "🎯 Завдання:", quest.objective_text]
    if status == "ACTIVE" and (quest.target_quantity > 1 or quest.quest_type is QuestType.QUEST_ITEM):
        lines += ["", "📈 Прогрес:", f"{min(progress,quest.target_quantity)}/{quest.target_quantity}"]
    if status == "ACTIVE" and quest.quest_type is QuestType.QUEST_ITEM and quest.quest_item is not None:
        if progress >= int(quest.quest_item.required_quantity):
            lines += ["", "✅ Знахідку отримано:", quest.quest_item.display_name]
        else:
            lines += ["", "🔎 Стан пошуку:", "Доказ ще не знайдено."]
    if status == "LOCKED":
        lines += ["", "🔒 Для відкриття:"]
        if quest.previous_quest_id:
            previous = STORY_QUEST_REGISTRY.get(quest.previous_quest_id)
            lines.append(f"• завершити квест {previous.number if previous else '?'} «{previous.title if previous else quest.previous_quest_id}»")
        lines.append(f"• досягти {quest.unlock_level} рівня")
    if status == "ACTIVE" and quest.quest_type is QuestType.QUEST_ITEM and quest.quest_item is not None and progress < int(quest.quest_item.required_quantity):
        lines += ["", "🧭 Де шукати:", f"Полювати в локації {resolve_story_quest_location_name(quest.location_id)}."]
    else:
        route_label = "🧭 Наступний крок:" if status == "ACTIVE" and quest.quest_type is QuestType.QUEST_ITEM else "🧭 Куди йти:"
        lines += ["", route_label, str(navigation.next_step_hint or navigation.objective_hint or quest.objective_text)]
    lines += ["", "🎁 Нагорода:", f"{quest.reward.exp} EXP", f"{float(quest.reward.gold):.2f} золота"]
    return {"text":"\n".join(lines),"keyboard":build_story_quest_detail_keyboard(quest_id=quest.quest_id,status=status,page=page)}


def register_story_quest_handlers(bot):

    # Stage 19.25.14: hierarchical story navigation. Legacy callbacks remain registered below.
    def _hierarchy_status_reader(user_id, quest):
        """Return the canonical lifecycle value from the UI-neutral quest view."""
        from systems.story_quest_system import get_story_quest_view
        stats = get_player_stats(user_id) or {}
        level = resolve_story_quest_player_level(stats)
        view = get_story_quest_view(
            db.conn,
            user_id=user_id,
            quest=quest,
            player_level=level,
        )
        status = str(view["status"]).casefold()
        if status in ("completed", "skipped"):
            return "completed"
        if status == "active":
            return "active"
        if status == "available":
            return "available"
        if status == "locked":
            return "locked"
        raise ValueError(f"Unknown story quest status: {status}")

    def _send_hierarchy(message, text, keyboard):
        return bot.send_message(message.chat.id, text, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: bool(parse_hierarchy_callback(call.data or "")))
    def story_quest_hierarchy_callback(call):
            action = parse_hierarchy_callback(call.data or "")
            if action is None:
                return
            user_id = call.from_user.id
            if action.kind == "index":
                text, keyboard = build_story_index(user_id, _hierarchy_status_reader)
            elif action.kind == "location":
                text, keyboard = build_section_index(str(action.value), user_id, _hierarchy_status_reader)
            elif action.kind == "section":
                text, keyboard = build_section_quests(str(action.value), user_id, _hierarchy_status_reader)
            elif action.kind == "quest":
                quest_number = int(action.value)
                quest = next((q for q in STORY_QUEST_REGISTRY.values() if q.number == quest_number), None)
                if quest is None:
                    bot.answer_callback_query(call.id, "Квест поки не активований.")
                    return
                stats = get_player_stats(user_id) or {}
                level = resolve_story_quest_player_level(stats)
                detail_snapshot = build_production_story_quest_detail(
                    db.conn,
                    user_id=user_id,
                    quest_id=quest.quest_id,
                    player_level=level,
                )
                text = detail_snapshot["text"]
                keyboard = _inline_markup(detail_snapshot["keyboard"])
                # Preserve existing quest actions and add an explicit hierarchy return route.
                keyboard.add(types.InlineKeyboardButton("🔙 Квести розділу", callback_data=section_callback_for_quest(quest_number)))
            else:
                bot.answer_callback_query(call.id, "Ця навігація вже неактуальна.")
                return
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            except Exception:
                _send_hierarchy(call.message, text, keyboard)
            bot.answer_callback_query(call.id)
    """Register the Profile journal route before broad downstream handlers.

    Stage 19.10 intentionally supports only open, refresh, and Profile return.
    Acceptance, navigation resolution, NPC interaction, and DB mutations remain
    unavailable until canonical production content and NPC registry exist.
    """
    from handlers.profile import send_profile_root
    import db
    from data.story_quest_content import STORY_QUEST_REGISTRY
    from db import get_player_stats
    from systems.story_quest_system import get_story_quest_view

    @bot.message_handler(
        func=lambda message: getattr(message, "text", None) == STORY_QUEST_BUTTON_TEXT
    )
    def story_quest_profile_reply(message):
        text, keyboard = build_story_index(message.from_user.id, _hierarchy_status_reader)
        return _send_hierarchy(message, text, keyboard)
        stats=get_player_stats(message.from_user.id) or {}
        level=resolve_story_quest_player_level(stats)
        items=[get_story_quest_view(db.conn,user_id=message.from_user.id,quest=q,player_level=level) for q in STORY_QUEST_REGISTRY.values()]
        snapshot=render_story_quest_journal(items)
        bot.send_message(message.chat.id,snapshot["text"],reply_markup=_inline_markup(snapshot["keyboard"]))

    @bot.callback_query_handler(
        func=lambda call: str(getattr(call, "data", "") or "").startswith(
            STORY_QUEST_CALLBACK_PREFIX
        )
    )
    def story_quest_callback(call):
        try:
            parsed = parse_story_quest_callback(call.data)
            if parsed.action in {"refresh", "page"}:
                stats=get_player_stats(call.from_user.id) or {}
                level=resolve_story_quest_player_level(stats)
                items=[get_story_quest_view(db.conn,user_id=call.from_user.id,quest=q,player_level=level) for q in STORY_QUEST_REGISTRY.values()]
                snapshot = render_story_quest_journal(items,page=int(parsed.value or 0) if parsed.action=="page" else 0)
                changed = _edit_story_journal_safely(
                    bot,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=snapshot["text"],
                    reply_markup=_inline_markup(snapshot["keyboard"]),
                )
                bot.answer_callback_query(
                    call.id,
                    "Журнал оновлено." if changed else "Журнал уже актуальний.",
                )
                return
            if parsed.action == "detail":
                stats=get_player_stats(call.from_user.id) or {}
                level=resolve_story_quest_player_level(stats)
                snapshot=build_production_story_quest_detail(db.conn,user_id=call.from_user.id,quest_id=parsed.value,player_level=level)
                _edit_story_journal_safely(bot,chat_id=call.message.chat.id,message_id=call.message.message_id,text=snapshot["text"],reply_markup=_inline_markup(snapshot["keyboard"]))
                bot.answer_callback_query(call.id)
                return
            if parsed.action == "navigate":
                stats=get_player_stats(call.from_user.id) or {}
                level=resolve_story_quest_player_level(stats)
                snapshot=build_production_story_quest_detail(db.conn,user_id=call.from_user.id,quest_id=parsed.value,player_level=level)
                bot.answer_callback_query(call.id,"Маршрут показано в деталях квесту.")
                return
            if parsed.action == "profile":
                bot.answer_callback_query(call.id)
                send_profile_root(bot, call.message.chat.id, call.from_user.id)
                return
            bot.answer_callback_query(call.id,"Некоректна дія журналу.",show_alert=True)
        except StoryQuestUiError:
            bot.answer_callback_query(
                call.id, "Некоректна дія журналу квестів.", show_alert=True
            )
