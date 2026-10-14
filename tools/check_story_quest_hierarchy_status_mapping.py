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
rows = [
    node for node in ast.walk(TREE)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "_hierarchy_status_reader"
]
assert len(rows) == 1
assert rows[0].col_offset > 0
segment = ast.get_source_segment(SOURCE, rows[0]) or ""
assert "get_story_quest_view" in segment
assert 'view["status"]' in segment
assert 'status in ("completed", "skipped")' in segment
assert 'status == "active"' in segment
assert 'status == "available"' in segment
assert 'status == "locked"' in segment
assert 'detail.get("status")' not in segment
assert "status_key" not in segment
compile(SOURCE, str(PATH), "exec")

from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_system import get_story_quest_view
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 31))
print("STORY QUEST HIERARCHY STATUS MAPPING: PASS")
