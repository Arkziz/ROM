#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Presentation-only hierarchy for the story quest journal.

Hierarchy: stories -> sections -> quests -> existing quest detail.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from telebot import types

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_hierarchy import (
    get_story_location,
    get_story_section,
    get_story_section_for_quest_number,
    ordered_story_locations,
    ordered_story_sections,
)

CALLBACK_PREFIX = "sqh:v1"
ROOT_CALLBACK = f"{CALLBACK_PREFIX}:index"


@dataclass(frozen=True, slots=True)
class HierarchyAction:
    kind: str
    value: str | int | None = None


def _callback(*parts: object) -> str:
    value = ":".join((CALLBACK_PREFIX, *(str(part) for part in parts)))
    if len(value.encode("utf-8")) > 64:
        raise ValueError(f"Story hierarchy callback is too long: {value}")
    return value


def parse_hierarchy_callback(data: str) -> HierarchyAction | None:
    if data == ROOT_CALLBACK:
        return HierarchyAction("index")
    if not data.startswith(f"{CALLBACK_PREFIX}:"):
        return None
    parts = data.split(":")
    if parts[:2] != ["sqh", "v1"]:
        return None
    if len(parts) == 4 and parts[2] == "loc":
        return HierarchyAction("location", parts[3])
    if len(parts) == 4 and parts[2] == "sec":
        return HierarchyAction("section", parts[3])
    if len(parts) == 4 and parts[2] == "q" and parts[3].isdigit():
        return HierarchyAction("quest", int(parts[3]))
    if len(parts) == 4 and parts[2] == "back" and parts[3] == "index":
        return HierarchyAction("index")
    return HierarchyAction("invalid")


def _registry_by_number() -> dict[int, object]:
    return {quest.number: quest for quest in STORY_QUEST_REGISTRY.values()}


def _completed_numbers(user_id: int, status_reader: Callable[[int, object], str]) -> set[int]:
    completed = set()
    for quest in STORY_QUEST_REGISTRY.values():
        if status_reader(user_id, quest) == "completed":
            completed.add(quest.number)
    return completed


def _status_icon(status: str) -> str:
    return {
        "completed": "✅",
        "active": "📖",
        "available": "✨",
        "locked": "🔒",
    }.get(status, "▫️")


def build_story_index(user_id: int, status_reader: Callable[[int, object], str]) -> tuple[str, types.InlineKeyboardMarkup]:
    rows = _registry_by_number()
    completed = _completed_numbers(user_id, status_reader)
    text = "📜 Сюжетні історії\n\nОберіть історію, яку хочете переглянути."
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for story in ordered_story_locations():
        story_numbers = [n for section in ordered_story_sections(story.location_id) for n in section.quest_numbers if n in rows]
        keyboard.add(types.InlineKeyboardButton(
            text=f"{story.button_label} · {len(completed.intersection(story_numbers))}/{len(story_numbers)}",
            callback_data=_callback("loc", story.location_id),
        ))
    return text, keyboard


def _section_status(user_id: int, section, status_reader: Callable[[int, object], str]) -> str:
    rows = _registry_by_number()
    statuses = [status_reader(user_id, rows[number]) for number in section.quest_numbers if number in rows]
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    if "active" in statuses:
        return "active"
    if "available" in statuses:
        return "available"
    return "locked"


def build_section_index(location_id: str, user_id: int, status_reader: Callable[[int, object], str]) -> tuple[str, types.InlineKeyboardMarkup]:
    story = get_story_location(location_id)
    sections = ordered_story_sections(location_id)
    rows = _registry_by_number()
    completed = _completed_numbers(user_id, status_reader)
    story_numbers = [n for section in sections for n in section.quest_numbers if n in rows]
    text = (
        f"{story.button_label}\n\n"
        f"Прогрес історії: {len(completed.intersection(story_numbers))}/{len(story_numbers)}\n\n"
        "Оберіть розділ:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for section in sections:
        status = _section_status(user_id, section, status_reader)
        completed_count = len(completed.intersection(section.quest_numbers))
        keyboard.add(types.InlineKeyboardButton(
            text=f"{_status_icon(status)} {section.display_title} · {completed_count}/{len(section.quest_numbers)}",
            callback_data=_callback("sec", section.section_id),
        ))
    keyboard.add(types.InlineKeyboardButton("🔙 Сюжетні історії", callback_data=ROOT_CALLBACK))
    return text, keyboard


def build_section_quests(section_id: str, user_id: int, status_reader: Callable[[int, object], str]) -> tuple[str, types.InlineKeyboardMarkup]:
    section = get_story_section(section_id)
    story = get_story_location(section.location_id)
    rows = _registry_by_number()
    completed = _completed_numbers(user_id, status_reader)
    visible_numbers = [number for number in section.quest_numbers if number in rows]
    text = (
        f"📖 {section.display_title}\n\n"
        f"Історія: {story.display_name}\n"
        f"Рівень розділу: {section.required_level}\n"
        f"Прогрес: {len(completed.intersection(visible_numbers))}/{len(visible_numbers)}\n\n"
        "Оберіть квест:"
    )
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for number in visible_numbers:
        quest = rows[number]
        status = status_reader(user_id, quest)
        keyboard.add(types.InlineKeyboardButton(
            text=f"{_status_icon(status)} {quest.number}. {quest.title}",
            callback_data=_callback("q", quest.number),
        ))
    keyboard.add(types.InlineKeyboardButton("🔙 Розділи", callback_data=_callback("loc", section.location_id)))
    keyboard.add(types.InlineKeyboardButton("📜 Сюжетні історії", callback_data=ROOT_CALLBACK))
    return text, keyboard


def section_callback_for_quest(quest_number: int) -> str:
    return _callback("sec", get_story_section_for_quest_number(quest_number).section_id)


def quest_callback(quest_number: int) -> str:
    return _callback("q", quest_number)
