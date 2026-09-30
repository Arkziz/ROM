#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical presentation metadata for hierarchical story quest navigation.

This module owns story and section grouping only. It does not render Telegram
UI, mutate quest state, or expose technical location IDs to players.
"""
from __future__ import annotations

from dataclasses import dataclass

from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_location_presentation import resolve_story_quest_location_name


@dataclass(frozen=True, slots=True)
class StorySectionMetadata:
    """One production-visible story section and its ordered quest numbers."""

    section_id: str
    location_id: str
    number: int
    title: str
    required_level: int
    quest_numbers: tuple[int, ...]
    sort_order: int

    @property
    def display_title(self) -> str:
        """Return the canonical Ukrainian player-facing section title."""
        return f"Розділ {self.number}. {self.title}"


@dataclass(frozen=True, slots=True)
class StoryLocationMetadata:
    """One production story grouped under a canonical game location."""

    story_id: str
    location_id: str
    icon: str
    sort_order: int
    section_ids: tuple[str, ...]

    @property
    def display_name(self) -> str:
        """Resolve the localized location name without formatting its ID."""
        return resolve_story_quest_location_name(self.location_id)

    @property
    def button_label(self) -> str:
        """Return the canonical player-facing story button label."""
        return f"{self.icon} {self.display_name}"


STORY_SECTIONS: dict[str, StorySectionMetadata] = {
    "start_path_01": StorySectionMetadata(
        section_id="start_path_01",
        location_id="start_path",
        number=1,
        title="Тривога на околиці",
        required_level=1,
        quest_numbers=tuple(range(1, 11)),
        sort_order=10,
    ),
    "start_path_02": StorySectionMetadata(
        section_id="start_path_02",
        location_id="start_path",
        number=2,
        title="Рунічна аномалія",
        required_level=2,
        quest_numbers=tuple(range(11, 21)),
        sort_order=20,
    ),
    "start_path_03": StorySectionMetadata(
        section_id="start_path_03",
        location_id="start_path",
        number=3,
        title="Зниклий патруль",
        required_level=3,
        quest_numbers=tuple(range(21, 31)),
        sort_order=30,
    ),
}


STORY_LOCATIONS: dict[str, StoryLocationMetadata] = {
    "start_path": StoryLocationMetadata(
        story_id="start_path",
        location_id="start_path",
        icon="🌄",
        sort_order=10,
        section_ids=("start_path_01", "start_path_02", "start_path_03"),
    ),
}


def ordered_story_locations() -> tuple[StoryLocationMetadata, ...]:
    """Return production stories in stable display order."""
    return tuple(sorted(STORY_LOCATIONS.values(), key=lambda story: story.sort_order))


def ordered_story_sections(location_id: str) -> tuple[StorySectionMetadata, ...]:
    """Return production sections for one location in stable display order."""
    story = STORY_LOCATIONS.get(location_id)
    if story is None:
        raise KeyError(f"Unknown story location: {location_id}")
    return tuple(sorted((STORY_SECTIONS[section_id] for section_id in story.section_ids), key=lambda section: section.sort_order))


def get_story_location(location_id: str) -> StoryLocationMetadata:
    """Return canonical story metadata or fail closed for an unknown ID."""
    try:
        return STORY_LOCATIONS[location_id]
    except KeyError as exc:
        raise KeyError(f"Unknown story location: {location_id}") from exc


def get_story_section(section_id: str) -> StorySectionMetadata:
    """Return canonical section metadata or fail closed for an unknown ID."""
    try:
        return STORY_SECTIONS[section_id]
    except KeyError as exc:
        raise KeyError(f"Unknown story section: {section_id}") from exc


def get_story_section_for_quest_number(quest_number: int) -> StorySectionMetadata:
    """Resolve exactly one production section for a production quest number."""
    matches = tuple(section for section in STORY_SECTIONS.values() if quest_number in section.quest_numbers)
    if len(matches) != 1:
        raise KeyError(f"Quest {quest_number} belongs to {len(matches)} story sections")
    return matches[0]


def validate_story_hierarchy_metadata() -> dict[str, object]:
    """Validate registry coverage, ordering, localization, and section contracts."""
    production_by_number = {quest.number: quest for quest in STORY_QUEST_REGISTRY.values()}
    production_numbers = tuple(production_by_number)
    metadata_numbers: list[int] = []
    seen_numbers: set[int] = set()

    if tuple(sorted(STORY_LOCATIONS, key=lambda location_id: STORY_LOCATIONS[location_id].sort_order)) != tuple(
        story.story_id for story in ordered_story_locations()
    ):
        raise ValueError("Story location ordering is not stable")

    for story in ordered_story_locations():
        if story.story_id != story.location_id:
            raise ValueError(f"Story ID must equal canonical location ID: {story.story_id}")
        if story.display_name != "Початок Шляху" and story.location_id == "start_path":
            raise ValueError("start_path must resolve to Початок Шляху")
        if story.location_id in story.button_label or "Start Path" in story.button_label:
            raise ValueError("Technical location ID leaked into player-facing story label")
        sections = ordered_story_sections(story.location_id)
        if tuple(section.section_id for section in sections) != story.section_ids:
            raise ValueError(f"Section order mismatch for {story.story_id}")
        expected_section_numbers = tuple(range(1, len(sections) + 1))
        if tuple(section.number for section in sections) != expected_section_numbers:
            raise ValueError(f"Section numbers must be continuous for {story.story_id}")

        for section in sections:
            if section.location_id != story.location_id:
                raise ValueError(f"Section {section.section_id} location mismatch")
            if "глава" in section.display_title.casefold():
                raise ValueError(f"Forbidden Ukrainian term in {section.section_id}")
            if not section.display_title.startswith("Розділ "):
                raise ValueError(f"Invalid section presentation title: {section.display_title}")
            if not section.quest_numbers:
                raise ValueError(f"Empty section: {section.section_id}")
            if section.quest_numbers != tuple(range(section.quest_numbers[0], section.quest_numbers[-1] + 1)):
                raise ValueError(f"Non-contiguous quest range: {section.section_id}")
            for quest_number in section.quest_numbers:
                if quest_number in seen_numbers:
                    raise ValueError(f"Quest {quest_number} belongs to multiple sections")
                seen_numbers.add(quest_number)
                metadata_numbers.append(quest_number)
                quest = production_by_number.get(quest_number)
                if quest is None:
                    raise ValueError(f"Metadata exposes inactive quest {quest_number}")
                if quest.location_id != story.location_id:
                    raise ValueError(f"Quest {quest_number} location mismatch")
                if quest.unlock_level != section.required_level:
                    raise ValueError(f"Quest {quest_number} unlock level mismatch")

    if tuple(metadata_numbers) != production_numbers:
        raise ValueError(
            f"Hierarchy coverage mismatch: metadata={tuple(metadata_numbers)}, production={production_numbers}"
        )

    return {
        "story_ids": tuple(story.story_id for story in ordered_story_locations()),
        "section_ids": tuple(section.section_id for section in STORY_SECTIONS.values()),
        "quest_numbers": tuple(metadata_numbers),
        "production_quest_count": len(production_numbers),
        "metadata_quest_count": len(metadata_numbers),
        "localized_start_path": STORY_LOCATIONS["start_path"].display_name,
        "start_path_button_label": STORY_LOCATIONS["start_path"].button_label,
        "section_titles": tuple(section.display_title for section in ordered_story_sections("start_path")),
    }


STORY_HIERARCHY_VALIDATION = validate_story_hierarchy_metadata()
