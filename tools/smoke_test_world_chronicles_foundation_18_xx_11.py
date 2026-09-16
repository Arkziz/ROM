# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from systems.world_chronicle_system import (
    get_world_chronicle_page,
    init_world_chronicle_system,
    record_world_chronicle_event,
)

with tempfile.TemporaryDirectory() as temporary_directory:
    database = Path(temporary_directory) / "world_chronicles.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, character_name TEXT)")
    connection.commit()
    connection.close()

    assert init_world_chronicle_system(database)["success"]
    assert init_world_chronicle_system(database)["success"]

    first = record_world_chronicle_event(
        "player_joined", 1, "Мандрівник", "player_joined:1", db_path=database
    )
    replay = record_world_chronicle_event(
        "player_joined", 1, "Мандрівник", "player_joined:1", db_path=database
    )
    assert first == {"success": True, "inserted": True}
    assert replay == {"success": True, "inserted": False}

    for index in range(104):
        result = record_world_chronicle_event(
            "player_level_up",
            1,
            "Мандрівник",
            f"player_level_up:1:{index + 2}",
            metadata={"level": index + 2},
            db_path=database,
        )
        assert result["success"]

    page_zero = get_world_chronicle_page(0, 10, database)
    page_nine = get_world_chronicle_page(9, 10, database)
    assert page_zero["total"] == 100
    assert len(page_zero["items"]) == 10
    assert page_zero["has_previous"] is False
    assert page_zero["has_next"] is True
    assert page_nine["has_previous"] is True
    assert page_nine["has_next"] is False
    assert page_zero["items"][0]["deduplication_key"] == "player_level_up:1:105"

    invalid = record_world_chronicle_event(
        "not_allowed", 1, "Мандрівник", "invalid:1", db_path=database
    )
    assert invalid["success"] is False

print("WORLD_CHRONICLES_FOUNDATION_18_XX_11_OK")
