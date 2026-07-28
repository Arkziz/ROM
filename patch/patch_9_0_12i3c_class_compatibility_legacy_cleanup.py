#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i3c: remove class compatibility legacy captures and old db implementations."""
from __future__ import annotations
import ast, base64, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
PATCH_ID="9.0.12i3c"
APIS=("can_equip_item_by_class","can_equip_inventory_item_by_class","is_inventory_item_class_compatible")
CAPTURES=tuple("_legacy_equipment_ro_v1_"+name for name in APIS)
SMOKE=base64.b64decode("IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJST00gOS4wLjEyaTNjOiBwb3N0LWNsZWFudXAgY2xhc3MgY29tcGF0aWJpbGl0eSBzbW9rZS10ZXN0LiIiIgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCmltcG9ydCBhc3QsIHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKUk9PVCA9IFBhdGgoX19maWxlX18pLnJlc29sdmUoKS5wYXJlbnRzWzFdCmlmIHN0cihST09UKSBub3QgaW4gc3lzLnBhdGg6IHN5cy5wYXRoLmluc2VydCgwLCBzdHIoUk9PVCkpCkFQSVMgPSAoImNhbl9lcXVpcF9pdGVtX2J5X2NsYXNzIiwgImNhbl9lcXVpcF9pbnZlbnRvcnlfaXRlbV9ieV9jbGFzcyIsICJpc19pbnZlbnRvcnlfaXRlbV9jbGFzc19jb21wYXRpYmxlIikKQ0FQVFVSRVMgPSB0dXBsZSgiX2xlZ2FjeV9lcXVpcG1lbnRfcm9fdjFfIiArIG5hbWUgZm9yIG5hbWUgaW4gQVBJUykKCmRlZiBmYWlsKG1zZyk6CiAgICBwcmludCgiW0ZBSUxdICIgKyBtc2cpOyByYWlzZSBTeXN0ZW1FeGl0KDEpCgpkZWYgZGVmcyhwYXRoKToKICAgIHRleHQ9cGF0aC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIpOyB0cmVlPWFzdC5wYXJzZSh0ZXh0LGZpbGVuYW1lPXN0cihwYXRoKSk7IG91dD17fQogICAgZm9yIG5vZGUgaW4gdHJlZS5ib2R5OgogICAgICAgIGlmIGlzaW5zdGFuY2Uobm9kZSwoYXN0LkZ1bmN0aW9uRGVmLGFzdC5Bc3luY0Z1bmN0aW9uRGVmKSk6IG91dC5zZXRkZWZhdWx0KG5vZGUubmFtZSxbXSkuYXBwZW5kKG5vZGUpCiAgICByZXR1cm4gdGV4dCxvdXQKCmRlZiBzYWZlX2NhbGwoZm4sKmFyZ3MpOgogICAgdHJ5OiByZXR1cm4gVHJ1ZSxmbigqYXJncykKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXhjOiByZXR1cm4gRmFsc2UsZiJ7dHlwZShleGMpLl9fbmFtZV9ffToge2V4Y30iCgpkZWYgbWFpbigpOgogICAgZGJfdGV4dCxkYl9kZWZzPWRlZnMoUk9PVC8iZGIucHkiKTsgZXFfdGV4dCxlcV9kZWZzPWRlZnMoUk9PVC8ic3lzdGVtcyIvImVxdWlwbWVudF9zeXN0ZW0ucHkiKQogICAgZm9yIG5hbWUgaW4gQVBJUzoKICAgICAgICBpZiBsZW4oZGJfZGVmcy5nZXQobmFtZSxbXSkpICE9IDE6IGZhaWwoZiJkYi5weToge25hbWV9IGRlZmluaXRpb25zICE9IDEiKQogICAgICAgIGlmIGxlbihlcV9kZWZzLmdldChuYW1lLFtdKSkgIT0gMTogZmFpbChmImVxdWlwbWVudF9zeXN0ZW0ucHk6IHtuYW1lfSBkZWZpbml0aW9ucyAhPSAxIikKICAgICAgICBkYl9zZWc9YXN0LmdldF9zb3VyY2Vfc2VnbWVudChkYl90ZXh0LGRiX2RlZnNbbmFtZV1bMF0pIG9yICIiCiAgICAgICAgZXFfc2VnPWFzdC5nZXRfc291cmNlX3NlZ21lbnQoZXFfdGV4dCxlcV9kZWZzW25hbWVdWzBdKSBvciAiIgogICAgICAgIGlmICJlcXVpcG1lbnRfc3lzdGVtIiBub3QgaW4gZGJfc2VnOiBmYWlsKGYiZGIue25hbWV9IGlzIG5vdCBhbiBlcXVpcG1lbnRfc3lzdGVtIHdyYXBwZXIiKQogICAgICAgIGlmICJfY2FsbF9sZWdhY3kiIGluIGVxX3NlZzogZmFpbChmImVxdWlwbWVudF9zeXN0ZW0ue3tuYW1lfX0gc3RpbGwgY2FsbHMgX2NhbGxfbGVnYWN5IikKICAgIGZvciBjYXB0dXJlIGluIENBUFRVUkVTOgogICAgICAgIGlmIGNhcHR1cmUgaW4gZGJfdGV4dDogZmFpbChmImxlZ2FjeSBjYXB0dXJlIHRleHQgcmVtYWluczoge2NhcHR1cmV9IikKICAgIGltcG9ydCBkYgogICAgZnJvbSBzeXN0ZW1zIGltcG9ydCBlcXVpcG1lbnRfc3lzdGVtIGFzIGVxCiAgICBtaXNzaW5nPXNhZmVfY2FsbChkYi5jYW5fZXF1aXBfaXRlbV9ieV9jbGFzcywtMSxOb25lKQogICAgaWYgbm90IG1pc3NpbmdbMF0gb3Igbm90IGlzaW5zdGFuY2UobWlzc2luZ1sxXSxkaWN0KSBvciBub3QgeyJzdWNjZXNzIiwibWVzc2FnZSJ9Lmlzc3Vic2V0KG1pc3NpbmdbMV0pOiBmYWlsKCJtaXNzaW5nLWl0ZW0gZGljdCBjb250cmFjdCBmYWlsZWQiKQogICAgbm9uX2VxPXNhZmVfY2FsbChkYi5jYW5fZXF1aXBfaXRlbV9ieV9jbGFzcywtMSx7ImNhdGVnb3J5IjoicG90aW9uIiwic2xvdF9rZXkiOk5vbmV9KQogICAgaWYgbm90IG5vbl9lcVswXSBvciBub25fZXFbMV0uZ2V0KCJzdWNjZXNzIikgaXMgbm90IFRydWU6IGZhaWwoIm5vbi1lcXVpcG1lbnQgY29udHJhY3QgZmFpbGVkIikKICAgIG1pc3NpbmdfYm9vbD1zYWZlX2NhbGwoZGIuaXNfaW52ZW50b3J5X2l0ZW1fY2xhc3NfY29tcGF0aWJsZSwtMSwtOTg3NjU0MzIxKQogICAgaWYgbm90IG1pc3NpbmdfYm9vbFswXSBvciBub3QgaXNpbnN0YW5jZShtaXNzaW5nX2Jvb2xbMV0sYm9vbCk6IGZhaWwoImJvb2xlYW4gaGVscGVyIGNvbnRyYWN0IGZhaWxlZCIpCiAgICBjdXJzb3I9ZGIuY29ubi5jdXJzb3IoKTsgY29tcGFyaXNvbnM9MDsgbWlzbWF0Y2hlcz1bXQogICAgdHJ5OgogICAgICAgIGN1cnNvci5leGVjdXRlKCJTRUxFQ1QgdXNlcl9pZCBGUk9NIHVzZXJzIE9SREVSIEJZIHVzZXJfaWQiKTsgdXNlcnM9W3JbMF0gZm9yIHIgaW4gY3Vyc29yLmZldGNoYWxsKCldCiAgICBleGNlcHQgRXhjZXB0aW9uOiB1c2Vycz1bXQogICAgZm9yIHVpZCBpbiB1c2VyczoKICAgICAgICBjdXJzb3IuZXhlY3V0ZSgiU0VMRUNUIGlkIEZST00gaW52ZW50b3J5IFdIRVJFIHVzZXJfaWQ9PyBPUkRFUiBCWSBpZCBMSU1JVCAyNSIsKHVpZCwpKQogICAgICAgIGZvciAoaWlkLCkgaW4gY3Vyc29yLmZldGNoYWxsKCk6CiAgICAgICAgICAgIGZvciBuYW1lIGluIEFQSVNbMTpdOgogICAgICAgICAgICAgICAgcHViPXNhZmVfY2FsbChnZXRhdHRyKGRiLG5hbWUpLHVpZCxpaWQpOyBzeXN2PXNhZmVfY2FsbChnZXRhdHRyKGVxLG5hbWUpLHVpZCxpaWQpOyBjb21wYXJpc29ucys9MQogICAgICAgICAgICAgICAgaWYgcHViICE9IHN5c3Y6IG1pc21hdGNoZXMuYXBwZW5kKCh1aWQsaWlkLG5hbWUscHViLHN5c3YpKQogICAgaWYgbWlzbWF0Y2hlczogZmFpbChmInB1YmxpYy9zeXN0ZW0gbWlzbWF0Y2g6IHttaXNtYXRjaGVzWzBdfSIpCiAgICBwcmludCgiW09LXSBlcXVpcG1lbnQgY2xhc3MgY29tcGF0aWJpbGl0eSBwb3N0LWNsZWFudXAiKQogICAgcHJpbnQoIi0gcHVibGljIEFQSXM6IDMiKQogICAgcHJpbnQoIi0gZGlyZWN0IHN5c3RlbSBpbXBsZW1lbnRhdGlvbnM6IDMiKQogICAgcHJpbnQoIi0gbGVnYWN5IGNhcHR1cmVzOiAwIikKICAgIHByaW50KGYiLSBydW50aW1lIGNvbXBhcmlzb25zOiB7Y29tcGFyaXNvbnN9IikKICAgIHByaW50KCItIG1pc21hdGNoZXM6IDAiKQogICAgcHJpbnQoIi0gYm9vbGVhbiBoZWxwZXIgY29udHJhY3Q6IE9LIikKICAgIHByaW50KCItIGRhdGFiYXNlIG11dGF0aW9uczogMCIpCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6IG1haW4oKQo=").decode("utf-8")

def fail(msg): print("❌ "+msg); raise SystemExit(1)
def root_dir():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"equipment_system.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def funcs(tree):
 out={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): out.setdefault(n.name,[]).append(n)
 return out
def start(n):
 ds=getattr(n,"decorator_list",[]) or []
 return min([n.lineno]+[d.lineno for d in ds])
def main():
 root=root_dir(); dbp=root/"db.py"; eqp=root/"systems"/"equipment_system.py"; tool=root/"tools"/"smoke_test_equipment_class_compatibility.py"
 source=dbp.read_text(encoding="utf-8-sig"); tree=ast.parse(source,filename=str(dbp)); fd=funcs(tree)
 if all(len(fd.get(n,[]))==1 for n in APIS) and all(c not in source for c in CAPTURES):
  print(f"ℹ️ Патч {PATCH_ID} уже застосовано."); return
 for name in APIS:
  if len(fd.get(name,[])) < 2: fail(f"Очікувалося щонайменше 2 визначення {name} до очищення.")
  final=ast.get_source_segment(source,fd[name][-1]) or ""
  if "equipment_system" not in final: fail(f"Фінальна {name} не є wrapper у equipment_system.")
 eqtext=eqp.read_text(encoding="utf-8-sig"); eqtree=ast.parse(eqtext); eqfd=funcs(eqtree)
 for name in APIS:
  if len(eqfd.get(name,[]))!=1: fail(f"equipment_system.{name}: неправильна кількість визначень.")
  if "_call_legacy" in (ast.get_source_segment(eqtext,eqfd[name][0]) or ""): fail(f"equipment_system.{name} ще залежить від legacy.")
 ranges=[]
 # Remove all old definitions, keep only final public wrapper.
 for name in APIS:
  for node in fd[name][:-1]: ranges.append((start(node),node.end_lineno,name))
 # Remove only top-level try blocks that assign one of the three exact captures.
 for node in tree.body:
  if isinstance(node,ast.Try):
   names=set()
   for sub in ast.walk(node):
    if isinstance(sub,ast.Name): names.add(sub.id)
   hits=names.intersection(CAPTURES)
   if hits:
    if len(hits)!=1: fail("Неоднозначний capture try-block.")
    ranges.append((node.lineno,node.end_lineno,next(iter(hits))))
 # Require exactly 3 capture blocks and at least 3 old definitions.
 capture_ranges=[r for r in ranges if r[2] in CAPTURES]
 if len(capture_ranges)!=3: fail(f"Capture-блоків знайдено {len(capture_ranges)} замість 3.")
 ordered=sorted(ranges)
 for a,b in zip(ordered,ordered[1:]):
  if b[0] <= a[1]: fail("Діапазони очищення перетинаються.")
 lines=source.splitlines(keepends=True)
 for a,b,_ in sorted(ranges,reverse=True): del lines[a-1:b]
 updated="".join(lines); utree=ast.parse(updated,filename=str(dbp)); ufd=funcs(utree)
 for name in APIS:
  if len(ufd.get(name,[]))!=1: fail(f"Після очищення {name} definitions != 1.")
 for cap in CAPTURES:
  if cap in updated: fail(f"Після очищення лишився {cap}.")
 backup_dir=root/"backup"; backup_dir.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
 dbbak=backup_dir/f"db.py_{PATCH_ID}_class_compatibility_legacy_cleanup_{stamp}.bak"; shutil.copy2(dbp,dbbak)
 toolbak=None
 if tool.exists(): toolbak=backup_dir/f"tools_smoke_test_equipment_class_compatibility.py_{PATCH_ID}_{stamp}.bak"; shutil.copy2(tool,toolbak)
 try:
  tmp=dbp.with_name(".db.i3c.tmp"); tmp.write_text(updated,encoding="utf-8"); os.replace(tmp,dbp)
  tool.write_text(SMOKE,encoding="utf-8")
  py_compile.compile(str(dbp),doraise=True); py_compile.compile(str(tool),doraise=True)
  result=subprocess.run([sys.executable,str(tool)],cwd=root)
  if result.returncode: raise RuntimeError(f"post-cleanup smoke exit code {result.returncode}")
 except Exception as exc:
  shutil.copy2(dbbak,dbp)
  if toolbak: shutil.copy2(toolbak,tool)
  elif tool.exists(): tool.unlink()
  fail(f"Перевірка не пройдена; файли відновлено: {exc}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print("✅ Видалено 3 legacy capture-блоки class compatibility.")
 print(f"✅ Видалено старих визначень із db.py: {sum(len(fd[n])-1 for n in APIS)}")
 print("✅ Залишено 3 публічні wrappers db.py -> systems/equipment_system.py.")
 print("✅ Оновлено post-cleanup smoke-test.")
 print("Резервні копії:")
 print("   "+str(dbbak.relative_to(root)))
 if toolbak: print("   "+str(toolbak.relative_to(root)))
 print("Перевірки:")
 print("   python -m py_compile ./db.py")
 print("   python ./tools/smoke_test_equipment_class_compatibility.py")
 print("   python ./tools/smoke_test_equipment_write_contracts.py")
 print("   python ./tools/smoke_test_equipment_readonly_core.py")
 print("   python ./tools/smoke_test_rom_core.py")
 print("   python ./tools/check_imports.py")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
