#!/usr/bin/env python3
"""Maintained pure check for the story-quest UI foundation."""
from __future__ import annotations

import sys
from pathlib import Path

ROM_ROOT = Path(__file__).resolve().parents[1]
if str(ROM_ROOT) not in sys.path:
    sys.path.insert(0, str(ROM_ROOT))

from handlers.story_quests import (
    STORY_QUEST_BUTTON_TEXT,
    StoryQuestUiError,
    build_story_quest_callback,
    build_story_quest_detail_keyboard,
    parse_story_quest_callback,
    render_story_quest_detail,
    render_story_quest_journal,
)


def main():
    assert STORY_QUEST_BUTTON_TEXT == "📜 Квести"
    callback = build_story_quest_callback("page", "2")
    assert callback == "story_quest:page:2"
    parsed = parse_story_quest_callback(callback)
    assert parsed.action == "page" and parsed.value == "2"
    try:
        parse_story_quest_callback("foreign:page:2")
    except StoryQuestUiError:
        pass
    else:
        raise AssertionError("foreign callback namespace accepted")

    empty = render_story_quest_journal([])
    assert "Журнал поки порожній" in empty["text"]
    assert empty["page"] == 0 and empty["total"] == 0
    assert empty["keyboard"][-1][0]["callback_data"] == "story_quest:profile"

    items = []
    statuses = ["LOCKED", "AVAILABLE", "ACTIVE", "COMPLETED", "SKIPPED"]
    for number in range(1, 13):
        items.append({
            "quest_id": f"q{number}", "number": number,
            "title": f"Quest {number}", "status": statuses[(number - 1) % 5],
            "progress": 1, "quest_item_quantity": 0, "target_quantity": 3,
        })
    first = render_story_quest_journal(items, page=0)
    second = render_story_quest_journal(items, page=1)
    assert first["has_next"] and not first["has_previous"]
    assert second["has_previous"] and not second["has_next"]
    assert len(first["visible_quest_ids"]) == 10
    assert len(second["visible_quest_ids"]) == 2
    assert "Прогрес: 1/3" in first["text"]

    available = build_story_quest_detail_keyboard(
        quest_id="q2", status="AVAILABLE", page=0,
    )
    active = build_story_quest_detail_keyboard(
        quest_id="q3", status="ACTIVE", page=0,
    )
    completed = build_story_quest_detail_keyboard(
        quest_id="q4", status="COMPLETED", page=0,
    )
    assert available[0][0]["callback_data"] == "story_quest:navigate:q2"
    assert active[0][0]["callback_data"] == "story_quest:navigate:q3"
    assert len(completed) == 1
    detail = render_story_quest_detail(items[2])
    assert "Quest 3" in detail["text"] and "Прогрес: 1/3" in detail["text"]
    print("[PASS] story quest UI foundation")


if __name__ == "__main__":
    main()
