#!/usr/bin/env python3
from pathlib import Path
import ast,json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
q=next(x for x in STORY_QUEST_REGISTRY.values() if x.number==40)
assert q.quest_type.value=="TURN_IN"
assert tuple(q.required_quest_items)==()
assert q.objective_text=="Доповісти Старості про відкритий шлях до лігва та готовність мисливського загону."
t=STORY_QUEST_TEXT[q.quest_id]
assert "Староста вислуховує доповідь" in t["completion_text"]
assert "Розділ «Вовча загроза» завершено" in t["completion_text"]
assert "Отже, лігво знайдено" not in t["acceptance_text"]
s=(ROOT/"handlers/story_quest_npc_runtime.py").read_text(encoding="utf-8")
tree=ast.parse(s)
constants=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
assert constants.count("🗣️ Доповісти Старості")==1
assert "📖 Почати розмову" in constants
assert "🎯 Завдання:" in constants
conditional_pairs=[]
for node in ast.walk(tree):
 if isinstance(node,ast.IfExp) and isinstance(node.test,ast.Attribute) and node.test.attr=="required_quest_items":
  body=node.body.value if isinstance(node.body,ast.Constant) else None
  other=node.orelse.value if isinstance(node.orelse,ast.Constant) else None
  conditional_pairs.append((body,other))
assert ("📦 Передати докази","📖 Почати розмову") in conditional_pairs
assert ("📦 Передати докази","🗣️ Доповісти Старості") in conditional_pairs
assert ("🔍 Висновок:","🎯 Завдання:") in conditional_pairs
# Item-backed TURN_IN definitions remain present and consuming.
for n in (35,38):
 x=next(v for v in STORY_QUEST_REGISTRY.values() if v.number==n)
 assert len(x.required_quest_items)==1 and x.required_quest_items[0].consume is True
print("STORY QUEST ITEMLESS TURN-IN FLOW: PASS")
