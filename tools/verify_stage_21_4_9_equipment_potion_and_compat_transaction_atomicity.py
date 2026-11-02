#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SPEC={'systems/equipment_system.py': [{'name': 'ensure_equipment_slots', 'line': 618}, {'name': '_equipment_write_ensure_slots_v5', 'line': 2103}, {'name': '_equipment_write_set_slot_v5', 'line': 2161}, {'name': 'set_inventory_item_durability', 'line': 3131}, {'name': 'apply_random_durability_wear_on_victory', 'line': 3427}], 'systems/potion_system.py': [{'name': 'use_potion_from_inventory', 'line': 525}], 'db_modules/inventory_compat.py': [{'name': 'seed_class_reset_sphere_item', 'line': 215}]}
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
print("PASS: Stage 21.4.9 exact owner anchors and rollback invariants")
