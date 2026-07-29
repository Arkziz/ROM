#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i8e: remove remaining undefined names from Auction buy flow."""
from __future__ import annotations
import ast, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i8e"
REPLACEMENTS=(
    ("AUCTION_HISTORY_PURCHASED", "AUCTION_HISTORY_SOLD"),
    ("format_auction_price(price)", "decimal_to_price_text(price)"),
    ("format_auction_price(buyer_gold)", "decimal_to_price_text(buyer_gold)"),
)
TESTS=("smoke_test_auction_lifecycle_contracts.py","smoke_test_rom_core.py","check_imports.py")

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"auction_house_system.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def run(r,p,label):
 x=subprocess.run([sys.executable,str(p)],cwd=r)
 if x.returncode: raise RuntimeError(f"{label} exit code {x.returncode}")
def defs(tree):
 result=set()
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): result.add(n.name)
  elif isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): result.add(n.id)
 return result
def main():
 r=root(); target=r/"systems"/"auction_house_system.py"; tools=r/"tools"; readiness=tools/"db_cleanup_readiness.py"
 for n in TESTS:
  if not (tools/n).is_file(): fail(f"Відсутній tools/{n}.")
 src=target.read_text(encoding="utf-8-sig")
 if all(old not in src for old,_ in REPLACEMENTS) and all(new in src for _,new in REPLACEMENTS):
  print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
  for n in TESTS: run(r,tools/n,n)
  return
 updated=src
 for old,new in REPLACEMENTS:
  count=updated.count(old)
  if count!=1: fail(f"Фрагмент {old!r}: знайдено {count}, очікувалося 1.")
  updated=updated.replace(old,new,1)
 tree=ast.parse(updated,filename=str(target)); defined=defs(tree)
 required={"AUCTION_HISTORY_SOLD","decimal_to_price_text","AUCTION_UNCLAIMED_RETENTION_DAYS_V2","_auction_plus_days_iso_v2"}
 missing=sorted(required-defined)
 if missing: fail(f"Після зміни відсутні потрібні globals/helpers: {missing}")
 forbidden={"AUCTION_HISTORY_PURCHASED","format_auction_price","add_days_iso","AUCTION_UNCLAIMED_RETENTION_DAYS"}
 loads={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
 bad=sorted(forbidden & loads)
 if bad: fail(f"У модулі залишилися невизначені runtime names: {bad}")
 b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
 backup=b/f"systems_auction_house_system.py_{PATCH_ID}_{stamp}.bak"; shutil.copy2(target,backup)
 temp=target.with_name(".auction_house_system.i8e.tmp")
 try:
  temp.write_text(updated,encoding="utf-8"); os.replace(temp,target); py_compile.compile(str(target),doraise=True)
  for n in TESTS: run(r,tools/n,n)
  x=subprocess.run([sys.executable,str(readiness)],cwd=r,text=True,capture_output=True); print(x.stdout,end="")
  if x.returncode: raise RuntimeError(f"readiness exit code {x.returncode}")
  for expected in ("definitions: 353","duplicates: 2","legacy_refs: 0","unsafe_delete: 0","maybe_cleanup_later: 2"):
   if expected not in x.stdout: raise RuntimeError(f"readiness не містить: {expected}")
 except Exception as e:
  shutil.copy2(backup,target)
  if temp.exists(): temp.unlink()
  fail(f"Перевірка не пройдена; auction_house_system.py відновлено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print("✅ AUCTION_HISTORY_PURCHASED замінено на визначений AUCTION_HISTORY_SOLD.")
 print("✅ Невизначений format_auction_price замінено на decimal_to_price_text.")
 print("✅ У buy_auction_lot_v2 більше немає відомих undefined Auction names.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r)}")
 print("Перевірки:")
 print("   python -m py_compile ./systems/auction_house_system.py")
 for n in TESTS: print(f"   python ./tools/{n}")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
