#!/usr/bin/env python3
"""Maintained pure check for the canonical story-quest NPC registry."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_npcs import (
    STORY_QUEST_NPCS,
    StoryQuestNpcRegistryError,
    get_missing_story_quest_npc_routes,
    get_story_quest_npc,
    resolve_story_quest_navigation,
    validate_story_quest_npc_references,
    validate_story_quest_npc_registry,
)


def expect_error(action):
    try:
        action()
    except StoryQuestNpcRegistryError:
        return
    raise AssertionError("invalid NPC registry operation was accepted")


def main():
    expected_ids = {
        "elder", "mercenary_head", "blacksmith", "alchemist",
        "rune_master", "trader", "bartender",
    }
    assert set(STORY_QUEST_NPCS) == expected_ids
    assert len(STORY_QUEST_NPCS) == 7

    elder = get_story_quest_npc("elder")
    assert elder.display_name == "Староста"
    assert elder.city_section_id == "townhall"
    assert elder.production_route_exists
    bartender = resolve_story_quest_navigation("bartender")
    assert bartender["route_text"] == "🏙️ Місто → 🍺 Таверна → 🍺 Бармен"
    assert bartender["route_labels"][-1] == bartender["button_label"]

    missing = get_missing_story_quest_npc_routes()
    assert missing == ()
    assert all(STORY_QUEST_NPCS[key].production_route_exists for key in {
        "blacksmith", "alchemist", "rune_master", "trader"
    })

    validate_story_quest_npc_references(
        giver_npc_id="bartender", turn_in_npc_id="elder"
    )
    expect_error(lambda: get_story_quest_npc("unknown"))
    duplicate = (
        STORY_QUEST_NPCS["elder"],
        replace(STORY_QUEST_NPCS["bartender"], npc_id="elder"),
    )
    expect_error(lambda: validate_story_quest_npc_registry(duplicate))
    bad_route = (
        replace(
            STORY_QUEST_NPCS["trader"],
            route_labels=("🏙️ Місто", "🛒 Торговий ряд", "Неправильна кнопка"),
        ),
    )
    expect_error(lambda: validate_story_quest_npc_registry(bad_route))
    print("[PASS] canonical story quest NPC registry")


if __name__ == "__main__":
    main()
