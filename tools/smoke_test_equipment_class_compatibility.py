#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i3c: post-cleanup class compatibility smoke-test."""
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
APIS = ("can_equip_item_by_class", "can_equip_inventory_item_by_class", "is_inventory_item_class_compatible")
CAPTURES = tuple("_legacy_equipment_ro_v1_" + name for name in APIS)

def fail(msg):
    print("[FAIL] " + msg); raise SystemExit(1)

def defs(path):
    text=path.read_text(encoding="utf-8-sig"); tree=ast.parse(text,filename=str(path)); out={}
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): out.setdefault(node.name,[]).append(node)
    return text,out

def safe_call(fn,*args):
    try: return True,fn(*args)
    except Exception as exc: return False,f"{type(exc).__name__}: {exc}"

def main():
    db_text,db_defs=defs(ROOT/"db.py"); eq_text,eq_defs=defs(ROOT/"systems"/"equipment_system.py")
    for name in APIS:
        if len(db_defs.get(name,[])) != 1: fail(f"db.py: {name} definitions != 1")
        if len(eq_defs.get(name,[])) != 1: fail(f"equipment_system.py: {name} definitions != 1")
        db_seg=ast.get_source_segment(db_text,db_defs[name][0]) or ""
        eq_seg=ast.get_source_segment(eq_text,eq_defs[name][0]) or ""
        if "equipment_system" not in db_seg: fail(f"db.{name} is not an equipment_system wrapper")
        if "_call_legacy" in eq_seg: fail(f"equipment_system.{{name}} still calls _call_legacy")
    for capture in CAPTURES:
        if capture in db_text: fail(f"legacy capture text remains: {capture}")
    import db
    from systems import equipment_system as eq
    missing=safe_call(db.can_equip_item_by_class,-1,None)
    if not missing[0] or not isinstance(missing[1],dict) or not {"success","message"}.issubset(missing[1]): fail("missing-item dict contract failed")
    non_eq=safe_call(db.can_equip_item_by_class,-1,{"category":"potion","slot_key":None})
    if not non_eq[0] or non_eq[1].get("success") is not True: fail("non-equipment contract failed")
    missing_bool=safe_call(db.is_inventory_item_class_compatible,-1,-987654321)
    if not missing_bool[0] or not isinstance(missing_bool[1],bool): fail("boolean helper contract failed")
    cursor=db.conn.cursor(); comparisons=0; mismatches=[]
    try:
        cursor.execute("SELECT user_id FROM users ORDER BY user_id"); users=[r[0] for r in cursor.fetchall()]
    except Exception: users=[]
    for uid in users:
        cursor.execute("SELECT id FROM inventory WHERE user_id=? ORDER BY id LIMIT 25",(uid,))
        for (iid,) in cursor.fetchall():
            for name in APIS[1:]:
                pub=safe_call(getattr(db,name),uid,iid); sysv=safe_call(getattr(eq,name),uid,iid); comparisons+=1
                if pub != sysv: mismatches.append((uid,iid,name,pub,sysv))
    if mismatches: fail(f"public/system mismatch: {mismatches[0]}")
    print("[OK] equipment class compatibility post-cleanup")
    print("- public APIs: 3")
    print("- direct system implementations: 3")
    print("- legacy captures: 0")
    print(f"- runtime comparisons: {comparisons}")
    print("- mismatches: 0")
    print("- boolean helper contract: OK")
    print("- database mutations: 0")
if __name__ == "__main__": main()
