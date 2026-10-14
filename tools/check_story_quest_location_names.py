#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quests import build_production_story_quest_detail
from systems.story_quest_location_presentation import resolve_story_quest_location_name


def schema(connection):
    connection.executescript("""
    CREATE TABLE user_story_quests(
        user_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER,
        target_quantity INTEGER, reward_claimed INTEGER,
        accepted_at TEXT, completed_at TEXT, skipped_at TEXT, skip_reason TEXT
    );
    CREATE TABLE user_story_quest_items(
        user_id INTEGER, quest_id TEXT, item_key TEXT, quantity INTEGER, updated_at TEXT
    );
    """)


def main():
    assert resolve_story_quest_location_name("start_path") == "Початок Шляху"
    try:
        resolve_story_quest_location_name("unknown_story_region")
    except KeyError:
        pass
    else:
        raise AssertionError("unknown location_id must fail closed")

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    schema(connection)
    quest = next(q for q in STORY_QUEST_REGISTRY.values() if q.number == 7)
    connection.execute(
        "INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",
        (quest.quest_id,),
    )
    text = build_production_story_quest_detail(
        connection,
        user_id=1,
        quest_id=quest.quest_id,
        player_level=5,
    )["text"]
    assert "Полювати в локації Початок Шляху." in text
    assert "Start Path" not in text and "start_path" not in text

    journal_source = (ROOT / "handlers" / "story_quests.py").read_text(encoding="utf-8-sig")
    assert '.replace("_", " ").title()' not in journal_source
    assert ".replace('_', ' ').title()" not in journal_source
    for definition in STORY_QUEST_REGISTRY.values():
        assert resolve_story_quest_location_name(definition.location_id)
    assert len(STORY_QUEST_REGISTRY) == 10
    assert not any(q.number == 11 for q in STORY_QUEST_REGISTRY.values())
    connection.close()
    print("STORY QUEST LOCATION NAMES: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
