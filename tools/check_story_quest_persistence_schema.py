#!/usr/bin/env python3
"""Maintained isolated check for migration 053 and its runner contract."""
from __future__ import annotations

import ast
import importlib.util
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


def load_migration():
    """Load migration 053 without importing production DB connection owners."""
    spec = importlib.util.spec_from_file_location("migration_053_check", MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load migration 053")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    source = MIGRATION.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(MIGRATION))
    compile(source, str(MIGRATION), "exec")
    top_level_functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert "up" in top_level_functions
    assert [arg.arg for arg in top_level_functions["up"].args.args] == ["conn"]
    assert "db_modules.connection" not in source
    assert ".commit(" not in source and ".rollback(" not in source

    module = load_migration()
    database = sqlite3.connect(":memory:")
    database.execute("PRAGMA foreign_keys=ON")
    database.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY)")
    module.up(database)

    tables = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    indexes = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    )}
    assert EXPECTED_TABLES <= tables
    assert EXPECTED_INDEXES <= indexes

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
    print("[PASS] story quest migration runner contract and schema")


if __name__ == "__main__":
    main()
