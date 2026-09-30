#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_19_25_12_story_quest_hierarchy_ui_audit.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["decision"] == "READY_FOR_STAGE_19_25_13_HIERARCHY_METADATA"
assert data["production_snapshot"]["quest_numbers"] == list(range(1, 31))
assert data["production_snapshot"]["by_location"]["start_path"] == list(range(1, 31))
assert [s["quest_numbers"] for s in data["production_sections"]] == [
    list(range(1, 11)), list(range(11, 21)), list(range(21, 31))
]
assert data["decisions"]["ukrainian_term"] == "розділ"
assert data["decisions"]["forbidden_user_term"] == "глава"
assert data["decisions"]["location_display_name"] == "Початок Шляху"
assert data["decisions"]["production_sections_only"] is True
assert data["decisions"]["database_migration_required"] is False
assert all(item["within_limit"] for item in data["proposed_callback_namespace"].values())
print("STORY QUEST HIERARCHY UI AUDIT: PASS")
