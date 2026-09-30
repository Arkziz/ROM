#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY

PATH = ROOT / "handlers/city.py"
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
q23, q24 = by[23], by[24]
assert (q23.turn_in_npc_id or q23.giver_npc_id) == 'trader'
assert q23.quest_type.value == "QUEST_ITEM"
assert q23.quest_item is not None and q23.quest_item.consume_on_completion is False
assert q24.quest_type.value == "TALK"
assert all(item.consume is False for item in q24.required_quest_items)

handlers = []
for fn in ast.walk(TREE):
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    segment = ast.get_source_segment(SOURCE, fn) or ""
    if "🛒 Торговий ряд" not in segment:
        continue
    hooks = []
    sends = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "send_story_npc_if_present":
                if any(isinstance(arg, ast.Constant) and arg.value == 'trader' for arg in node.args):
                    hooks.append(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"send_message", "reply_to", "reply"}:
                sends.append(node)
    if hooks:
        handlers.append((fn, hooks, sends, segment))
assert handlers
handlers.sort(key=lambda row: ((row[0].end_lineno or row[0].lineno) - row[0].lineno, row[0].lineno))
fn, hooks, sends, segment = handlers[0]
assert len(hooks) == 1
# The Trade Row handler may delegate the service message to a helper. The hook
# must still be the final top-level action, or immediately precede a return.
top_level = list(fn.body)
hook_stmt = next(stmt for stmt in top_level if any(node is hooks[0] for node in ast.walk(stmt)))
hook_index = top_level.index(hook_stmt)
assert hook_index == len(top_level) - 1 or isinstance(top_level[hook_index + 1], ast.Return)
assert "Продати весь мотлох" in SOURCE
assert "Продати спорядження" in SOURCE
assert "Базове спорядження" in SOURCE
print("MERCHANT STORY INTEGRATION: PASS")
