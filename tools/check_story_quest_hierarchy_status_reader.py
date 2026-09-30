#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATH = ROOT / "handlers/story_quests.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
rows = [n for n in ast.walk(TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_hierarchy_status_reader"]
assert len(rows) == 1
assert rows[0].col_offset > 0
segment = ast.get_source_segment(SOURCE, rows[0]) or ""
assert "stats = get_player_stats(user_id) or {}" in segment
assert "level = resolve_story_quest_player_level(stats)" in segment
assert "db.conn" in segment
assert "user_id=user_id" in segment
assert "quest_id=quest.quest_id" in segment
assert "player_level=level" in segment
assert "build_production_story_quest_detail(user_id" not in segment
compile(SOURCE, str(PATH), "exec")
import handlers.story_quests
import handlers.story_quest_hierarchy_ui
print("STORY QUEST HIERARCHY STATUS READER: PASS")
