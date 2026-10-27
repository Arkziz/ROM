#!/usr/bin/env python3
import ast, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
root_text=str(ROOT)
if root_text not in sys.path: sys.path.insert(0,root_text)
DOMAIN=ROOT/"rom_v2/domain/six_class_simulation_matrix.py"
TEST=ROOT/"tests_v2/test_six_class_simulation_matrix.py"
for p in (DOMAIN,TEST):
    if not p.is_file(): raise SystemExit(f"FAIL: missing {p.relative_to(ROOT)}")
source=DOMAIN.read_text(encoding="utf-8")
tree=ast.parse(source)
for forbidden in ("sqlite3","aiogram","telegram","systems.simulation"):
    if forbidden in source: raise SystemExit(f"FAIL: forbidden dependency {forbidden}")
classes=("warrior","knight","scout","rogue","mage","priest")
if any(name not in source for name in classes): raise SystemExit("FAIL: incomplete class matrix")
result=subprocess.run([sys.executable,"-m","unittest","tests_v2.test_six_class_simulation_matrix","-v"],cwd=ROOT)
if result.returncode: raise SystemExit(result.returncode)
print("PASS: Stage 21.15.4c six-class short-probe matrix; long run not executed")
