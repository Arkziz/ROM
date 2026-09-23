#!/usr/bin/env python3
"""Maintained isolated integration check for the story-quest persistence API."""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROM_ROOT = Path(__file__).resolve().parents[1]
if str(ROM_ROOT) not in sys.path:
    sys.path.insert(0, str(ROM_ROOT))

from db_modules.story_quests import (
    StoryQuestConflictError,
    activate_story_quest,
    add_story_quest_item,
    get_active_story_quest,
    get_story_quest_item_quantity,
    list_story_quest_journal,
    set_story_quest_progress,
    skip_active_story_quest,
)


def apply_schema(connection):
    """Apply migration 053 to the temporary database through up(conn)."""
    path = ROM_ROOT / "migrations" / "053_story_quest_persistence_schema.py"
    spec = importlib.util.spec_from_file_location("migration_053_api_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.up(connection)


def expect_conflict(action):
    try:
        action()
    except StoryQuestConflictError:
        return
    raise AssertionError("expected StoryQuestConflictError")


def main():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY)")
    apply_schema(db)
    db.execute("INSERT INTO users(user_id) VALUES (1)")

    first = activate_story_quest(
        db, user_id=1, quest_id="fixture_one", quest_number=1,
        target_quantity=3, timestamp="2026-01-01T00:00:00+00:00",
    )
    assert first["status"] == "ACTIVE" and first["progress"] == 0
    assert activate_story_quest(
        db, user_id=1, quest_id="fixture_one", quest_number=1,
        target_quantity=3, timestamp="ignored",
    )["id"] == first["id"]
    expect_conflict(lambda: activate_story_quest(
        db, user_id=1, quest_id="fixture_two", quest_number=2,
        target_quantity=1,
    ))

    assert set_story_quest_progress(
        db, user_id=1, quest_id="fixture_one", progress=2,
    )["progress"] == 2
    assert set_story_quest_progress(
        db, user_id=1, quest_id="fixture_one", progress=99,
    )["progress"] == 3
    expect_conflict(lambda: set_story_quest_progress(
        db, user_id=1, quest_id="fixture_one", progress=1,
    ))

    item = add_story_quest_item(
        db, user_id=1, quest_id="fixture_one", item_key="fixture_item",
        quantity=2, required_quantity=3,
    )
    assert item == {"granted": 2, "quantity": 2, "required_quantity": 3}
    capped = add_story_quest_item(
        db, user_id=1, quest_id="fixture_one", item_key="fixture_item",
        quantity=20, required_quantity=3,
    )
    assert capped == {"granted": 1, "quantity": 3, "required_quantity": 3}
    assert get_story_quest_item_quantity(db, 1, "fixture_one", "fixture_item") == 3

    skipped = skip_active_story_quest(db, user_id=1, quest_id="fixture_one")
    assert skipped["status"] == "SKIPPED"
    assert get_active_story_quest(db, 1) is None
    assert get_story_quest_item_quantity(db, 1, "fixture_one", "fixture_item") == 0
    assert len(list_story_quest_journal(db, 1)) == 1
    expect_conflict(lambda: add_story_quest_item(
        db, user_id=1, quest_id="fixture_one", item_key="fixture_item",
        quantity=1, required_quantity=3,
    ))
    assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    db.close()
    print("[PASS] story quest persistence API")


if __name__ == "__main__":
    main()
