from __future__ import annotations
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'tools/run_single_class_progression.py';s=p.read_text(encoding='utf-8-sig');tree=ast.parse(s);compile(tree,str(p),'exec');assert "reports'/'simulation'/'single_class" in s;assert "choices=range(2,11)" in s;assert "equipment_summary" in s and "equipment_details" in s;assert "PARTIAL" in s and "max_days_reached" in s
print('[PASS] parallel-safe single-class runner contract')
