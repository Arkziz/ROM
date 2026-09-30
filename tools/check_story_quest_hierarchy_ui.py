#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_hierarchy import STORY_LOCATIONS, ordered_story_sections
from handlers.story_quest_hierarchy_ui import (
    ROOT_CALLBACK,
    build_section_index,
    build_section_quests,
    build_story_index,
    parse_hierarchy_callback,
    section_callback_for_quest,
)

assert STORY_LOCATIONS["start_path"].button_label == "🌿 Початок Шляху"
assert tuple(section.quest_numbers for section in ordered_story_sections("start_path")) == (
    tuple(range(1, 11)), tuple(range(11, 21)), tuple(range(21, 31))
)
assert parse_hierarchy_callback(ROOT_CALLBACK).kind == "index"
assert parse_hierarchy_callback("sqh:v1:loc:start_path").kind == "location"
assert parse_hierarchy_callback("sqh:v1:sec:start_path_03").kind == "section"
assert parse_hierarchy_callback("sqh:v1:q:30").value == 30
assert parse_hierarchy_callback("legacy:quest:1") is None
assert len(section_callback_for_quest(30).encode("utf-8")) <= 64

status = lambda user_id, quest: "completed" if quest.number <= 30 else "locked"
index_text, index_kb = build_story_index(1, status)
assert index_text.startswith("📜 Сюжетні історії")
assert len(index_kb.keyboard) == 1
assert index_kb.keyboard[0][0].text.startswith("🌿 Початок Шляху")
section_text, section_kb = build_section_index("start_path", 1, status)
assert "Оберіть розділ" in section_text
assert len(section_kb.keyboard) == 4
assert [row[0].text for row in section_kb.keyboard[:3]] == [
    "✅ Розділ 1. Тривога на околиці · 10/10",
    "✅ Розділ 2. Рунічна аномалія · 10/10",
    "✅ Розділ 3. Зниклий патруль · 10/10",
]
quests_text, quests_kb = build_section_quests("start_path_03", 1, status)
assert "Розділ 3. Зниклий патруль" in quests_text
assert len(quests_kb.keyboard) == 12
assert all("31." not in row[0].text for row in quests_kb.keyboard)

handler = (ROOT / "handlers/story_quests.py").read_text(encoding="utf-8")
tree = ast.parse(handler)
assert "story_quest_hierarchy_callback" in handler
assert "Квести розділу" in handler
assert "build_story_index(message.from_user.id" in handler
assert "STORY_HIERARCHY_ROOT_CALLBACK" in handler
assert "глава" not in (ROOT / "handlers/story_quest_hierarchy_ui.py").read_text(encoding="utf-8").casefold()
compile(handler, "handlers/story_quests.py", "exec")
print("STORY QUEST HIERARCHY UI: PASS")
