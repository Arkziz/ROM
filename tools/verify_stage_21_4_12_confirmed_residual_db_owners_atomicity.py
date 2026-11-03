#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SPEC={'db_modules/character.py': [{'name': 'spend_user_mp', 'line': 128}, {'name': 'restore_user_mp_to_full', 'line': 187}], 'db_modules/generated_equipment.py': [{'name': 'create_generated_equipment_item_for_slot', 'line': 366}], 'db_modules/inventory.py': [{'name': 'compact_user_item_stacks', 'line': 226}, {'name': 'sell_all_trash', 'line': 406}], 'db_modules/player.py': [{'name': 'create_user', 'line': 132}], 'db_modules/quests.py': [{'name': 'get_user_daily_quest', 'line': 41}, {'name': 'add_daily_quest_progress', 'line': 91}, {'name': 'process_daily_quest_progress_on_kill', 'line': 292}], 'db_modules/shop.py': [{'name': 'create_common_equipment_shop_preview', 'line': 190}, {'name': 'cancel_common_equipment_shop_preview', 'line': 448}]}
def calls_owned(fn):
 out=[]
 class V(ast.NodeVisitor):
  def visit_FunctionDef(self,node):
   if node is fn:
    for stmt in node.body: self.visit(stmt)
  def visit_AsyncFunctionDef(self,node): return
  def visit_Lambda(self,node): return
  def visit_Call(self,node): out.append(node); self.generic_visit(node)
 V().visit(fn); return out
for rel,anchors in SPEC.items():
 tree=ast.parse((ROOT/rel).read_text(encoding="utf-8-sig"))
 for anchor in anchors:
  matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==anchor["name"] and n.lineno==anchor["line"]]; assert len(matches)==1,(rel,anchor,len(matches)); fn=matches[0]; calls=calls_owned(fn); attrs=[c.func.attr for c in calls if isinstance(c.func,ast.Attribute)]
  assert attrs.count("commit")>=1,(rel,anchor,attrs); assert attrs.count("rollback")>=1,(rel,anchor,attrs)
  assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(x,ast.Raise) for x in ast.walk(h)) for h in ast.walk(fn)),(rel,anchor)
print("PASS: Stage 21.4.12 exact residual DB owner anchors and rollback invariants")
