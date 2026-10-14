#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATH = ROOT / "data/story_quests/start_path_21_30.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
rows_nodes = []
for node in TREE.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "QUEST_ROWS" for t in node.targets):
        rows_nodes.append(node.value)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "QUEST_ROWS":
        rows_nodes.append(node.value)
assert len(rows_nodes) == 1
rows = ast.literal_eval(rows_nodes[0])
assert isinstance(rows, tuple) and len(rows) == 10
assert tuple(row["definition"]["number"] for row in rows) == tuple(range(21, 31))
assert len(SOURCE.splitlines()) > 100
assert max(len(line) for line in SOURCE.splitlines()) <= 240
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 31))
print("START PATH 21-30 READABLE FORMAT: PASS")
