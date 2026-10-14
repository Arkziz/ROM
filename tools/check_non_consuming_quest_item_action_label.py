#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.story_quest_content import STORY_QUEST_REGISTRY

PATH = ROOT / "handlers/story_quest_npc_runtime.py"
SOURCE = PATH.read_text(encoding="utf-8")
ast.parse(SOURCE, filename=str(PATH))
compile(SOURCE, str(PATH), "exec")
assert '✅ Передати доказ' not in SOURCE
assert SOURCE.count('🔍 Показати доказ') >= 2
by = {q.number: q for q in STORY_QUEST_REGISTRY.values()}
q23, q24, q30 = by[23], by[24], by[30]
assert q23.quest_type.value == "QUEST_ITEM"
assert q23.quest_item is not None and q23.quest_item.consume_on_completion is False
assert q24.quest_type.value == "TALK"
assert all(item.consume is False for item in q24.required_quest_items)
assert q30.quest_type.value == "TURN_IN"
assert len(q30.required_quest_items) == 3 and all(item.consume is True for item in q30.required_quest_items)
print("NON-CONSUMING QUEST ITEM ACTION LABEL: PASS")
