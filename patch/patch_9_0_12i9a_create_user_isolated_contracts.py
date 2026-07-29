#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i9a: install isolated create_user contracts."""
from __future__ import annotations
import py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i9a"
TOOL_NAME="smoke_test_create_user_contracts.py"
TOOL=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated runtime contracts for the final db.create_user implementation."""
from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db

TEST_USER_ID=-90120901
EXPECTED_SLOTS={"main_hand","off_hand","helmet","shoulders","chest","gloves","legs","boots","necklace","ring"}


def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
def columns(table): return [row[1] for row in db.conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
def user_tables():
 result=[]
 for (name,) in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
  try:
   if "user_id" in columns(name): result.append(name)
  except Exception: pass
 return result
def cleanup():
 priority=["equipment_slots","inventory","auction_lots"]
 tables=user_tables()
 for table in priority+[x for x in tables if x not in priority and x!="users"]:
  try: db.conn.execute(f'DELETE FROM "{table}" WHERE user_id=?',(TEST_USER_ID,))
  except Exception: pass
 try: db.conn.execute("DELETE FROM users WHERE user_id=?",(TEST_USER_ID,))
 except Exception: pass
 db.conn.commit()
def snapshot_real():
 cols=columns("users")
 quoted=",".join(f'"{x}"' for x in cols)
 rows=[tuple(r) for r in db.conn.execute(f'SELECT {quoted} FROM users WHERE user_id>=0 ORDER BY user_id').fetchall()]
 return cols,rows
def main():
 source=(ROOT/"db.py").read_text(encoding="utf-8-sig"); tree=ast.parse(source); definitions=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=="create_user": definitions.append(node)
 if len(definitions)!=3: fail(f"create_user definitions={len(definitions)}, expected 3")
 final=definitions[-1]; final_source=ast.get_source_segment(source,final) or ""
 for marker in ("init_energy_system","ensure_equipment_slots","migrate_legacy_equipment_to_slots","expand_bag_slots_to_40"):
  if marker not in final_source: fail(f"final create_user missing {marker}")

 # Avoid hidden global mutation from expand_bag_slots_to_40.
 low_bags=db.conn.execute("SELECT user_id,bag_slots FROM users WHERE user_id>=0 AND COALESCE(bag_slots,0)<40").fetchall()
 if low_bags: fail(f"real users with bag_slots<40 must be reviewed before test: {low_bags}")
 before=snapshot_real(); cleanup(); checks=0
 try:
  db.create_user(TEST_USER_ID)
  cols=columns("users"); row=db.conn.execute("SELECT * FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()
  if not row: fail("fixture user was not created")
  data=dict(zip(cols,row))
  expected={"hp":170,"max_hp":170,"level":1,"exp":0,"gold":0.0,"kills":0,"bag_slots":40,
            "current_location":"start_path","str":10,"dex":10,"intelligence":10,"wis":10,"sta":10,
            "energy":0,"energy_full_notified":1}
  for key,value in expected.items():
   if key not in data: fail(f"users schema missing {key}")
   if data[key]!=value: fail(f"default {key}={data[key]!r}, expected {value!r}")
  if not str(data.get("last_energy_update") or ""): fail("last_energy_update is empty")
  checks+=len(expected)+1

  slots=db.conn.execute("SELECT slot_key,inventory_id FROM equipment_slots WHERE user_id=?",(TEST_USER_ID,)).fetchall()
  if {r[0] for r in slots}!=EXPECTED_SLOTS: fail(f"equipment slots mismatch: {slots}")
  if any(r[1] is not None for r in slots): fail("new user has equipped inventory_id")
  checks+=2

  # INSERT OR IGNORE must preserve existing progress.
  db.conn.execute("UPDATE users SET gold=123.45,level=3,exp=77,hp=111,energy=7 WHERE user_id=?",(TEST_USER_ID,)); db.conn.commit()
  db.create_user(TEST_USER_ID)
  preserved=db.conn.execute("SELECT gold,level,exp,hp,energy FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()
  if tuple(preserved)!=(123.45,3,77,111,7): fail(f"repeat create_user overwrote progress: {tuple(preserved)}")
  count=db.conn.execute("SELECT COUNT(*) FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()[0]
  slot_count=db.conn.execute("SELECT COUNT(*) FROM equipment_slots WHERE user_id=?",(TEST_USER_ID,)).fetchone()[0]
  if count!=1 or slot_count!=10: fail(f"idempotency counts user={count}, slots={slot_count}")
  checks+=2

  # Final implementation intentionally repairs invalid fatigue only.
  db.conn.execute("UPDATE users SET energy=99 WHERE user_id=?",(TEST_USER_ID,)); db.conn.commit()
  db.create_user(TEST_USER_ID)
  repaired=db.conn.execute("SELECT energy,energy_full_notified,last_energy_update FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()
  if int(repaired[0])!=0 or int(repaired[1])!=1 or not str(repaired[2] or ""): fail(f"invalid energy repair failed: {tuple(repaired)}")
  checks+=1
 finally:
  cleanup()
 after=snapshot_real()
 if before!=after: fail("real user rows changed")
 if db.conn.execute("SELECT COUNT(*) FROM users WHERE user_id=?",(TEST_USER_ID,)).fetchone()[0]: fail("fixture user cleanup failed")
 if db.conn.execute("SELECT COUNT(*) FROM equipment_slots WHERE user_id=?",(TEST_USER_ID,)).fetchone()[0]: fail("fixture slot cleanup failed")
 print("[OK] create_user isolated contracts")
 print(f"- contract checks: {checks}")
 print("- defaults and energy fields: OK")
 print("- equipment slots: 10")
 print("- repeated creation idempotency: OK")
 print("- invalid energy repair: OK")
 print("- isolated fixture cleanup: OK")
 print("- real user mutations: 0")
if __name__=="__main__": main()
'''

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"tools"/"db_cleanup_readiness.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def main():
 r=root(); target=r/"tools"/TOOL_NAME; backup=None
 if target.exists() and target.read_text(encoding="utf-8-sig")!=TOOL:
  b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); backup=b/f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"; shutil.copy2(target,backup)
 target.write_text(TOOL,encoding="utf-8")
 try:
  py_compile.compile(str(target),doraise=True)
  result=subprocess.run([sys.executable,str(target)],cwd=r)
  if result.returncode: raise RuntimeError(f"contract test exit code {result.returncode}")
 except Exception as e:
  if backup: shutil.copy2(backup,target)
  elif target.exists(): target.unlink()
  fail(f"Контрактні тести не пройдено; встановлення відкочено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Створено: tools/{TOOL_NAME}")
 print("✅ Тимчасового користувача та його слоти видалено.")
 print("✅ Реальні користувачі не змінені.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r) if backup else 'не потрібні - новий файл'}")
 print("Перевірки:")
 print(f"   python ./tools/{TOOL_NAME}")
 print("   python ./tools/smoke_test_energy_contracts.py")
 print("   python ./tools/smoke_test_rom_core.py")
 print("   python ./tools/check_imports.py")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
