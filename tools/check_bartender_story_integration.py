#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY

PATH = ROOT / 'handlers/city.py'
SOURCE = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(PATH))
assert '📜 Нових сюжетних доручень зараз немає. Перевір журнал квестів або повернися пізніше.' not in SOURCE
rows = [n for n in ast.walk(TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == 'show_story_bartender']
assert len(rows) == 1
fn = rows[0]
hooks = []
sends = []
for node in ast.walk(fn):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "send_story_npc_if_present":
            if any(isinstance(arg, ast.Constant) and arg.value == 'bartender' for arg in node.args):
                hooks.append(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"send_message", "reply_to", "reply"}:
            sends.append(node)
assert len(hooks) == 1 and sends
assert min((s.end_lineno or s.lineno) for s in sends) < hooks[0].lineno
by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
q27, q28 = by[27], by[28]
assert q27.quest_type.value == "TALK"
assert q27.giver_npc_id == 'bartender'
assert q28.previous_quest_id == q27.quest_id
compile(SOURCE, str(PATH), "exec")
print("BARTENDER STORY INTEGRATION: PASS")
