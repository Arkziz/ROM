#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i3b: real class compatibility in equipment_system."""
import ast, base64, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
PATCH_ID="9.0.12i3b"
OLD=base64.b64decode("ZGVmIGNhbl9lcXVpcF9pdGVtX2J5X2NsYXNzKCphcmdzLCAqKmt3YXJncyk6CiAgICByZXR1cm4gX2NhbGxfbGVnYWN5KCdjYW5fZXF1aXBfaXRlbV9ieV9jbGFzcycsICphcmdzLCAqKmt3YXJncykKCmRlZiBjYW5fZXF1aXBfaW52ZW50b3J5X2l0ZW1fYnlfY2xhc3MoKmFyZ3MsICoqa3dhcmdzKToKICAgIHJldHVybiBfY2FsbF9sZWdhY3koJ2Nhbl9lcXVpcF9pbnZlbnRvcnlfaXRlbV9ieV9jbGFzcycsICphcmdzLCAqKmt3YXJncykKCmRlZiBpc19pbnZlbnRvcnlfaXRlbV9jbGFzc19jb21wYXRpYmxlKCphcmdzLCAqKmt3YXJncyk6CiAgICByZXR1cm4gX2NhbGxfbGVnYWN5KCdpc19pbnZlbnRvcnlfaXRlbV9jbGFzc19jb21wYXRpYmxlJywgKmFyZ3MsICoqa3dhcmdzKQo=").decode("utf-8")
NEW=base64.b64decode("IyDinIUgUk9NIDkuMC4xMmkzYjogUkVBTCBDTEFTUy1DT01QQVRJQklMSVRZIElNUExFTUVOVEFUSU9OCiMgVGhlc2UgdGhyZWUgcHVibGljIGRvbWFpbiBmdW5jdGlvbnMgbm8gbG9uZ2VyIGRlbGVnYXRlIHRocm91Z2gKIyBfbGVnYWN5X2VxdWlwbWVudF9yb192MV8qIGNhcHR1cmVzLiBMb3ctbGV2ZWwgY2xhc3NpZmljYXRpb24gYW5kIHJ1bGUgaGVscGVycwojIHJlbWFpbiBhdmFpbGFibGUgdGhyb3VnaCBkYi5weSBjb21wYXRpYmlsaXR5IEFQSXMgdW50aWwgdGhlaXIgb3duIGV4dHJhY3Rpb24uCgpkZWYgY2FuX2VxdWlwX2l0ZW1fYnlfY2xhc3ModXNlcl9pZCwgaXRlbV9pbmZvKToKICAgIGRiID0gX2RiKCkKCiAgICBpZiBub3QgaXRlbV9pbmZvOgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJzdWNjZXNzIjogRmFsc2UsCiAgICAgICAgICAgICJtZXNzYWdlIjogIuKdjCDQn9GA0LXQtNC80LXRgiDQvdC1INC30L3QsNC50LTQtdC90L4uIgogICAgICAgIH0KCiAgICBpZiBpdGVtX2luZm8uZ2V0KCJjYXRlZ29yeSIpICE9ICJlcXVpcG1lbnQiOgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJzdWNjZXNzIjogVHJ1ZSwKICAgICAgICAgICAgIm1lc3NhZ2UiOiAiIgogICAgICAgIH0KCiAgICBjbGFzc19rZXkgPSBkYi5nZXRfY2hhcmFjdGVyX2NsYXNzKHVzZXJfaWQpCiAgICBpZiBub3QgY2xhc3Nfa2V5OgogICAgICAgIHJldHVybiB7CiAgICAgICAgICAgICJzdWNjZXNzIjogRmFsc2UsCiAgICAgICAgICAgICJtZXNzYWdlIjogIuKdjCDQodC/0L7Rh9Cw0YLQutGDINC+0LHQtdGA0Lgg0LrQu9Cw0YEg0L/QtdGA0YHQvtC90LDQttCwLiIKICAgICAgICB9CgogICAgY2hlY2tzID0gKAogICAgICAgIGRiLmNoZWNrX2FybW9yX2NvbXBhdGliaWxpdHlfZm9yX2NsYXNzLAogICAgICAgIGRiLmNoZWNrX21haW5faGFuZF9jb21wYXRpYmlsaXR5X2Zvcl9jbGFzcywKICAgICAgICBkYi5jaGVja19vZmZfaGFuZF9jb21wYXRpYmlsaXR5X2Zvcl9jbGFzcywKICAgICkKICAgIGZvciBjaGVjayBpbiBjaGVja3M6CiAgICAgICAgcmVzdWx0ID0gY2hlY2soY2xhc3Nfa2V5LCBpdGVtX2luZm8pCiAgICAgICAgaWYgbm90IHJlc3VsdFsic3VjY2VzcyJdOgogICAgICAgICAgICByZXR1cm4gcmVzdWx0CgogICAgcmVzdWx0ID0gZGIuY2hlY2tfdHdvX2hhbmRlZF9jb25mbGljdF9mb3JfZXF1aXAodXNlcl9pZCwgaXRlbV9pbmZvKQogICAgaWYgbm90IHJlc3VsdFsic3VjY2VzcyJdOgogICAgICAgIHJldHVybiByZXN1bHQKCiAgICByZXR1cm4gewogICAgICAgICJzdWNjZXNzIjogVHJ1ZSwKICAgICAgICAibWVzc2FnZSI6ICIiCiAgICB9CgoKZGVmIGNhbl9lcXVpcF9pbnZlbnRvcnlfaXRlbV9ieV9jbGFzcyh1c2VyX2lkLCBpbnZlbnRvcnlfaWQpOgogICAgZGIgPSBfZGIoKQogICAgaXRlbV9pbmZvID0gZGIuZ2V0X2l0ZW1fY2xhc3NpZmljYXRpb25fYnlfaW52ZW50b3J5X2lkKGludmVudG9yeV9pZCkKICAgIHJldHVybiBjYW5fZXF1aXBfaXRlbV9ieV9jbGFzcyh1c2VyX2lkLCBpdGVtX2luZm8pCgoKZGVmIGlzX2ludmVudG9yeV9pdGVtX2NsYXNzX2NvbXBhdGlibGUodXNlcl9pZCwgaW52ZW50b3J5X2lkKToKICAgIHJlc3VsdCA9IGNhbl9lcXVpcF9pbnZlbnRvcnlfaXRlbV9ieV9jbGFzcyh1c2VyX2lkLCBpbnZlbnRvcnlfaWQpCiAgICByZXR1cm4gYm9vbChyZXN1bHQuZ2V0KCJzdWNjZXNzIikpCg==").decode("utf-8")

def fail(msg):
 print("❌ "+msg); raise SystemExit(1)

def main():
 here=Path(__file__).resolve(); root=None
 for candidate in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  candidate=candidate.resolve()
  if (candidate/"db.py").is_file() and (candidate/"systems"/"equipment_system.py").is_file(): root=candidate; break
 if root is None: fail("Не знайдено корінь ROM.")
 target=root/"systems"/"equipment_system.py"
 source=target.read_text(encoding="utf-8-sig")
 if NEW in source and OLD not in source:
  print(f"ℹ️ Патч {PATCH_ID} уже застосовано.")
  return
 if source.count(OLD)!=1:
  fail(f"Очікуваний legacy-блок знайдено {source.count(OLD)} разів замість 1. Файл не змінено.")
 updated=source.replace(OLD,NEW,1)
 try: ast.parse(updated,filename=str(target))
 except SyntaxError as exc: fail(f"AST-перевірка не пройдена: {exc}")
 # Ensure the three functions exist once and no longer call _call_legacy.
 tree=ast.parse(updated); names=("can_equip_item_by_class","can_equip_inventory_item_by_class","is_inventory_item_class_compatible")
 for name in names:
  nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
  if len(nodes)!=1: fail(f"Функція {name} має {len(nodes)} визначень у equipment_system.py.")
  segment=ast.get_source_segment(updated,nodes[0]) or ""
  if "_call_legacy" in segment: fail(f"Функція {name} все ще викликає _call_legacy.")
 backup_dir=root/"backup"; backup_dir.mkdir(exist_ok=True)
 stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
 backup=backup_dir/f"systems_equipment_system.py_{PATCH_ID}_class_compatibility_real_implementation_{stamp}.bak"
 shutil.copy2(target,backup)
 temp=target.with_name(".equipment_system.i3b.tmp")
 try:
  temp.write_text(updated,encoding="utf-8")
  os.replace(temp,target)
  py_compile.compile(str(target),doraise=True)
  # Audit tool is mandatory from i3a and compares new system behavior to captures.
  audit=root/"tools"/"smoke_test_equipment_class_compatibility.py"
  if not audit.is_file(): raise RuntimeError("відсутній tools/smoke_test_equipment_class_compatibility.py")
  result=subprocess.run([sys.executable,str(audit)],cwd=root)
  if result.returncode: raise RuntimeError(f"class compatibility audit exit code {result.returncode}")
  report=root/"DB_CLEANUP_9_0_12I3A_CLASS_COMPATIBILITY_AUDIT.md"
  if not report.is_file(): raise RuntimeError("аудит не створив звіт")
  report_text=report.read_text(encoding="utf-8-sig")
  if "- Mismatches: 0." not in report_text: raise RuntimeError("public/system/legacy мають розбіжності")
  if "- Boolean helper contract passed: True." not in report_text: raise RuntimeError("boolean helper contract не пройдено")
 except Exception as exc:
  shutil.copy2(backup,target)
  if temp.exists(): temp.unlink()
  fail(f"Перевірка не пройдена; equipment_system.py відновлено: {exc}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print("✅ Три class-compatibility API реалізовані безпосередньо в systems/equipment_system.py.")
 print("✅ Делегування цих API через _call_legacy прибрано.")
 print("✅ Legacy captures у db.py збережено для контрольного порівняння.")
 print("✅ Аудит public/system/legacy пройдено.")
 print("Резервні копії:")
 print("   "+str(backup.relative_to(root)))
 print("Перевірки:")
 print("   python -m py_compile ./systems/equipment_system.py")
 print("   python ./tools/smoke_test_equipment_class_compatibility.py")
 print("   python ./tools/smoke_test_equipment_write_contracts.py")
 print("   python ./tools/smoke_test_rom_core.py")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
