#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source=(ROOT/"handlers/story_quest_npc_runtime.py").read_text(encoding="utf-8")
tree=ast.parse(source)
def fn(name):
 rows=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert len(rows)==1
 return rows[0]
def qrefs(node):
 return [n for n in ast.walk(node) if isinstance(n,ast.Attribute) and n.attr=="required_quest_items" and isinstance(n.value,ast.Name) and n.value.id=="quest"]
def drefs(node):
 return [n for n in ast.walk(node) if isinstance(n,ast.Attribute) and n.attr=="required_quest_items" and isinstance(n.value,ast.Name) and n.value.id=="definition"]
label=fn("_turn_in_item_action_label");text=fn("_turn_in_text")
assert not qrefs(label) and len(drefs(label))>=1
assert not qrefs(text) and len(drefs(text))==1
constants=[n.value for n in ast.walk(label) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
for value in ("📦 Передати докази","📖 Почати розмову","🗣️ Доповісти Старості"):
 assert value in constants
# Evaluate only the pure helper AST in isolation and verify both branches.
module=ast.Module(body=[label],type_ignores=[]);ast.fix_missing_locations(module);ns={};exec(compile(module,"<label-helper>","exec"),ns)
class D:
 def __init__(self,items):self.required_quest_items=items
assert ns["_turn_in_item_action_label"](D(()),active=False)=="📖 Почати розмову"
assert ns["_turn_in_item_action_label"](D(()),active=True)=="🗣️ Доповісти Старості"
assert ns["_turn_in_item_action_label"](D((object(),object())),active=False)=="📦 Передати докази"
assert ns["_turn_in_item_action_label"](D((object(),object())),active=True)=="📦 Передати докази"
from data.story_quest_content import STORY_QUEST_REGISTRY
q=next(x for x in STORY_QUEST_REGISTRY.values() if x.number==40)
assert q.quest_type.value=="TURN_IN" and tuple(q.required_quest_items)==()
print("STORY QUEST ITEMLESS TURN-IN ACTION LABEL SCOPE: PASS")
