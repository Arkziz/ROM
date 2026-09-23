#!/usr/bin/env python3
"""Static and isolated-SQLite checks for migration 053.

The checker extracts SQL from the migration AST and applies it only to an
in-memory SQLite database. Production game.db is never opened.
"""
from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

ROM_ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROM_ROOT / "migrations" / "053_story_quest_persistence_schema.py"
EXPECTED_TABLES = {"user_story_quests", "user_story_quest_items"}
EXPECTED_INDEXES = {
    "ux_user_story_quests_one_active",
    "ix_user_story_quests_journal",
    "ix_user_story_quest_items_owner",
}


def extract_sql_statements(source: str) -> list[str]:
    """Return literal cursor.execute SQL in source order without importing it."""
    tree = ast.parse(source, filename=str(MIGRATION))
    statements = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "execute" or not node.args:
            continue
        try:
            value = ast.literal_eval(node.args[0])
        except Exception:
            continue
        if isinstance(value, str):
            statements.append(value)
    return statements


def main() -> None:
    source = MIGRATION.read_text(encoding="utf-8-sig")
    compile(source, str(MIGRATION), "exec")
    statements = extract_sql_statements(source)
    assert len(statements) == 5, statements

    database = sqlite3.connect(":memory:")
    database.execute("PRAGMA foreign_keys=ON")
    database.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY)")
    for statement in statements:
        database.execute(statement)

    tables = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    indexes = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    )}
    assert EXPECTED_TABLES <= tables
    assert EXPECTED_INDEXES <= indexes

    # Verify the composite FK has a valid parent key and cascades on reset.
    database.execute("INSERT INTO users(user_id) VALUES (1)")
    database.execute(
        """INSERT INTO user_story_quests
        (user_id,quest_id,quest_number,status,progress,target_quantity,
         reward_claimed,started_at,updated_at)
        VALUES (1,'fixture_quest',1,'ACTIVE',0,1,0,'t','t')"""
    )
    database.execute(
        """INSERT INTO user_story_quest_items
        (user_id,quest_id,item_key,quantity,updated_at)
        VALUES (1,'fixture_quest','fixture_item',1,'t')"""
    )

    try:
        database.execute(
            """INSERT INTO user_story_quests
            (user_id,quest_id,quest_number,status,progress,target_quantity,
             reward_claimed,started_at,updated_at)
            VALUES (1,'fixture_second',2,'ACTIVE',0,1,0,'t','t')"""
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("multiple ACTIVE quests were accepted")

    database.execute("DELETE FROM users WHERE user_id=1")
    assert database.execute("SELECT COUNT(*) FROM user_story_quests").fetchone()[0] == 0
    assert database.execute("SELECT COUNT(*) FROM user_story_quest_items").fetchone()[0] == 0
    assert database.execute("PRAGMA foreign_key_check").fetchall() == []
    database.close()
    print("[PASS] story quest persistence schema")


if __name__ == "__main__":
    main()
