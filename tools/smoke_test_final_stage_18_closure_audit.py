from __future__ import annotations
import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'tools/run_final_stage_18_closure_audit.py';s=p.read_text(encoding='utf-8-sig');ast.parse(s);compile(s,str(p),'exec')
for x in ('PRAGMA quick_check','PRAGMA foreign_key_check','042_attribute_points_foundation.py','accepted_risks','manual_acceptance_required','duplicate auto-escape notification defect is already fixed'):assert x in s
assert "mode=ro" in s and "sqlite3.connect(uri,uri=True)" in s and "TemporaryDirectory" in s and "copy2" in s
assert 'DELETE FROM' not in s and 'UPDATE ' not in s and 'INSERT INTO' not in s
print('[PASS] final closure audit read-only contract')
