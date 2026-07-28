#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i7c: remove earlier Dynamic Equipment and Repair Read definitions."""
from __future__ import annotations
import ast, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i7c"
DYNAMIC=(
"init_dynamic_equipment_system","get_dynamic_weapon_name","generate_dynamic_equipment_stats",
"create_generated_equipment_item","create_generated_equipment_item_for_slot",
"detect_weapon_profile_from_name","get_random_loot_armor_type","pick_weighted_stat",
"get_existing_primary_stat_budget","clear_primary_stat_bonuses","add_primary_stat_to_stats",
"apply_armor_type_primary_stat_profile_to_stats")
REPAIR="get_equipped_items_for_repair"
TARGETS=DYNAMIC+(REPAIR,)
PRESERVE=("init_auction_house","update_expired_auction_lots","create_user","claim_contract_reward")
CAPTURE="_base_get_equipped_items_for_repair_before_refine_display_v1"
TESTS=(
"smoke_test_dynamic_equipment_repair_contracts.py","smoke_test_equipment_readonly_core.py",
"smoke_test_inventory_refine_contracts.py","smoke_test_weapon_damage_contracts.py",
"smoke_test_equipment_write_contracts.py","smoke_test_equipment_durability_contracts.py",
"smoke_test_equipment_trader_contracts.py","smoke_test_player_combat_stats.py",
"smoke_test_rom_core.py","check_imports.py")

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"tools"/"db_cleanup_readiness.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def fmap(tree):
 d={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): d.setdefault(n.name,[]).append(n)
 return d
def start(n): return min([n.lineno]+[x.lineno for x in getattr(n,"decorator_list",[])])
def run(r,p,label):
 x=subprocess.run([sys.executable,str(p)],cwd=r)
 if x.returncode: raise RuntimeError(f"{label} exit code {x.returncode}")
def main():
 r=root(); dbp=r/"db.py"; tools=r/"tools"; readiness=tools/"db_cleanup_readiness.py"
 for name in TESTS:
  if not (tools/name).is_file(): fail(f"Відсутній tools/{name}.")
 src=dbp.read_text(encoding="utf-8-sig"); tree=ast.parse(src,filename=str(dbp)); defs=fmap(tree)
 if all(len(defs.get(n,[]))==1 for n in TARGETS) and CAPTURE not in src:
  print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
  for name in TESTS: run(r,tools/name,name)
  return
 preserve_before={n:len(defs.get(n,[])) for n in PRESERVE}
 if any(v<2 for v in preserve_before.values()): fail(f"Неочікуваний стан збережених груп: {preserve_before}")
 remove=[]; removed={}
 for name in DYNAMIC:
  nodes=defs.get(name,[])
  if len(nodes)<2: fail(f"db.py {name}: definitions={len(nodes)}, expected >=2")
  removed[name]=len(nodes)-1
  for node in nodes[:-1]: remove.append((start(node),node.end_lineno,name))
 # Repair Read: retain only final equipment_system wrapper and remove obsolete capture chain.
 nodes=defs.get(REPAIR,[])
 if len(nodes)!=3: fail(f"db.py {REPAIR}: definitions={len(nodes)}, expected 3")
 final=ast.get_source_segment(src,nodes[-1]) or ""
 if "equipment_system" not in final: fail("final repair-read definition is not equipment_system wrapper")
 removed[REPAIR]=2
 for node in nodes[:-1]: remove.append((start(node),node.end_lineno,REPAIR))
 capture_nodes=[]
 for node in tree.body:
  if isinstance(node,ast.Try):
   names={x.id for x in ast.walk(node) if isinstance(x,ast.Name)}
   if CAPTURE in names: capture_nodes.append(node)
 if len(capture_nodes)!=1: fail(f"repair-read capture blocks={len(capture_nodes)}, expected 1")
 cap=capture_nodes[0]; remove.append((cap.lineno,cap.end_lineno,CAPTURE))
 # Ensure no ranges overlap.
 ordered=sorted(remove)
 for a,b in zip(ordered,ordered[1:]):
  if b[0]<=a[1]: fail(f"Діапазони перетинаються: {a[2]} / {b[2]}")
 lines=src.splitlines(keepends=True)
 for a,b,_ in sorted(remove,reverse=True): del lines[a-1:b]
 updated="".join(lines); utree=ast.parse(updated,filename=str(dbp)); udefs=fmap(utree)
 for name in TARGETS:
  if len(udefs.get(name,[]))!=1: fail(f"Після очищення {name}: definitions={len(udefs.get(name,[]))}")
 if CAPTURE in updated: fail("Залишився obsolete repair-read capture")
 if {n:len(udefs.get(n,[])) for n in PRESERVE}!=preserve_before: fail("Патч зачепив інші 4 duplicate groups")
 duplicates={n for n,v in udefs.items() if len(v)>1}
 if duplicates!=set(PRESERVE): fail(f"Після очищення неочікувані duplicates: {sorted(duplicates)}")
 bdir=r/"backup"; bdir.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
 backup=bdir/f"db.py_{PATCH_ID}_dynamic_equipment_repair_cleanup_{stamp}.bak"; shutil.copy2(dbp,backup)
 temp=dbp.with_name(".db.i7c.tmp")
 try:
  temp.write_text(updated,encoding="utf-8"); os.replace(temp,dbp); py_compile.compile(str(dbp),doraise=True)
  for name in TESTS: run(r,tools/name,name)
  result=subprocess.run([sys.executable,str(readiness)],cwd=r,text=True,capture_output=True)
  print(result.stdout,end="")
  if result.returncode: raise RuntimeError(f"readiness exit code {result.returncode}")
  for expected in ("duplicates: 4","legacy_refs: 0","unsafe_delete: 0","maybe_cleanup_later: 4"):
   if expected not in result.stdout: raise RuntimeError(f"readiness missing {expected}")
 except Exception as e:
  shutil.copy2(backup,dbp)
  if temp.exists(): temp.unlink()
  fail(f"Перевірка не пройдена; db.py відновлено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Видалено ранніх Dynamic Equipment/Repair Read визначень: {sum(removed.values())}")
 print("✅ Видалено obsolete Repair Read capture block.")
 print("✅ Залишилося duplicate groups: 4.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r)}")
 print("Перевірки:")
 print("   python -m py_compile ./db.py")
 for name in TESTS: print(f"   python ./tools/{name}")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
