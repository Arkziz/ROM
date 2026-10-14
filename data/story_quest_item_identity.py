#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identity policy for virtual story-quest items outside ordinary inventory."""
from __future__ import annotations
import re

STORY_QUEST_ITEM_TABLE = "user_story_quest_items"
STORY_QUEST_ITEM_IDENTITY_COLUMNS = ("user_id", "quest_id", "item_key")
STORY_QUEST_ITEM_REQUIRED_COLUMNS = frozenset(
    {"id", "user_id", "quest_id", "item_key", "quantity", "updated_at"}
)
STORY_QUEST_ITEM_FORBIDDEN_COLUMNS = frozenset({"item_id", "inventory_id"})
STORY_QUEST_ITEM_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")


def validate_story_quest_item_key(item_key: str) -> str:
    """Return a stable canonical key or reject an inventory-like identity."""
    key = str(item_key or "").strip()
    if not STORY_QUEST_ITEM_KEY_PATTERN.fullmatch(key):
        raise ValueError(
            "story quest item_key must be lowercase snake_case with a namespace prefix"
        )
    return key


def inspect_story_quest_item_schema(connection) -> dict:
    """Inspect SQLite metadata without changing schema or table contents."""
    columns = tuple(
        str(row[1]) for row in connection.execute(
            f"PRAGMA table_info({STORY_QUEST_ITEM_TABLE})"
        ).fetchall()
    )
    column_set = frozenset(columns)
    indexes = connection.execute(
        f"PRAGMA index_list({STORY_QUEST_ITEM_TABLE})"
    ).fetchall()
    unique_column_sets = []
    for row in indexes:
        if not bool(row[2]):
            continue
        name = str(row[1])
        members = tuple(
            str(item[2]) for item in connection.execute(
                f"PRAGMA index_info({name})"
            ).fetchall()
        )
        unique_column_sets.append(members)
    foreign_keys = connection.execute(
        f"PRAGMA foreign_key_list({STORY_QUEST_ITEM_TABLE})"
    ).fetchall()
    return {
        "columns": columns,
        "missing_required": sorted(STORY_QUEST_ITEM_REQUIRED_COLUMNS - column_set),
        "forbidden_present": sorted(STORY_QUEST_ITEM_FORBIDDEN_COLUMNS & column_set),
        "identity_unique": STORY_QUEST_ITEM_IDENTITY_COLUMNS in unique_column_sets,
        "foreign_key_tables": sorted({str(row[2]) for row in foreign_keys}),
        "row_id_semantics": "local_table_row_only",
        "ordinary_items_id_used": False,
    }


def validate_story_quest_item_schema(connection) -> dict:
    """Fail closed if virtual quest items can overlap ordinary inventory identity."""
    result = inspect_story_quest_item_schema(connection)
    errors = []
    if result["missing_required"]:
        errors.append(f"missing columns: {result['missing_required']}")
    if result["forbidden_present"]:
        errors.append(f"forbidden columns: {result['forbidden_present']}")
    if not result["identity_unique"]:
        errors.append("missing UNIQUE(user_id, quest_id, item_key)")
    if "user_story_quests" not in result["foreign_key_tables"]:
        errors.append("missing foreign key to user_story_quests")
    if errors:
        raise RuntimeError("; ".join(errors))
    result["status"] = "PASS"
    return result
