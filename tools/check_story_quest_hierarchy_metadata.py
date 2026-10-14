#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_hierarchy import (
    STORY_HIERARCHY_VALIDATION,
    STORY_LOCATIONS,
    STORY_SECTIONS,
    get_story_section_for_quest_number,
    ordered_story_sections,
    validate_story_hierarchy_metadata,
)

result = validate_story_hierarchy_metadata()
assert result == STORY_HIERARCHY_VALIDATION
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 31))
assert result["story_ids"] == ("start_path",)
assert result["section_ids"] == ("start_path_01", "start_path_02", "start_path_03")
assert result["quest_numbers"] == tuple(range(1, 31))
assert result["localized_start_path"] == "Початок Шляху"
assert result["start_path_button_label"] == "🌿 Початок Шляху"
assert result["section_titles"] == (
    "Розділ 1. Тривога на околиці",
    "Розділ 2. Рунічна аномалія",
    "Розділ 3. Зниклий патруль",
)
assert tuple(section.quest_numbers for section in ordered_story_sections("start_path")) == (
    tuple(range(1, 11)), tuple(range(11, 21)), tuple(range(21, 31))
)
assert tuple(section.required_level for section in ordered_story_sections("start_path")) == (1, 2, 3)
assert get_story_section_for_quest_number(1).section_id == "start_path_01"
assert get_story_section_for_quest_number(15).section_id == "start_path_02"
assert get_story_section_for_quest_number(30).section_id == "start_path_03"
assert 31 not in result["quest_numbers"]
assert all("глава" not in section.display_title.casefold() for section in STORY_SECTIONS.values())
assert "start_path" not in STORY_LOCATIONS["start_path"].button_label
print("STORY QUEST HIERARCHY METADATA: PASS")
