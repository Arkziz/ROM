from __future__ import annotations
import ast,json,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'tools/audit_guild_resources_and_drop_pipeline_18_30_14a.py';s=p.read_text(encoding='utf-8-sig');ast.parse(s);compile(s,str(p),'exec')
assert "'normal':8500" in s and "'elite':1400" in s and "'boss':100" in s
assert "'normal':10000" in s and "'elite':10000" in s and "'boss':10000" in s
assert "'total_kills':40000" in s and "'guild_month_days':30" in s and "'guild_member_counts':[1,10]" in s
assert 'game.db' not in s and 'sqlite3' not in s
print('[PASS] Stage 18.30.14a audit contract and approved workloads')
