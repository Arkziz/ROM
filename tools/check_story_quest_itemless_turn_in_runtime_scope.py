#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source=(ROOT/"handlers/story_quest_npc_runtime.py").read_text(encoding="utf-8")
tree=ast.parse(source)
fn=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="_turn_in_text")
assert not any(isinstance(n,ast.Name) and n.id=="quest" and isinstance(getattr(n,"ctx",None),ast.Load) for n in ast.walk(fn))
refs=[n for n in ast.walk(fn) if isinstance(n,ast.Attribute) and n.attr=="required_quest_items" and isinstance(n.value,ast.Name) and n.value.id=="definition"]
assert len(refs)==1
constants=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
assert "🎯 Завдання:" in constants
assert "🗣️ Доповісти Старості" in constants
assert "📦 Передати докази" in constants
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
q=next(x for x in STORY_QUEST_REGISTRY.values() if x.number==40)
assert q.quest_type.value=="TURN_IN" and tuple(q.required_quest_items)==()
assert "Староста вислуховує доповідь" in STORY_QUEST_TEXT[q.quest_id]["completion_text"]
print("STORY QUEST ITEMLESS TURN-IN RUNTIME SCOPE: PASS")
