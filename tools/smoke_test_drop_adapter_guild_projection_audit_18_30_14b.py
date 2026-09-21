from __future__ import annotations
import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'tools/audit_drop_adapter_and_guild_projection_contract_18_30_14b.py';s=p.read_text(encoding='utf-8-sig');ast.parse(s);compile(s,str(p),'exec')
for x in ('process_enemy_drops','award_guild_elite_kill','award_guild_contract_completion','DAILY_CONTRACT_LIMIT','ELITE_CHANCE_PERCENT','BOSS_ENCOUNTER_CHANCE_PERCENT'):assert x in s
assert "'normal':8500" in s and "'elite':1400" in s and "'boss':100" in s and "'total_drop_sample':40000" in s
assert 'sqlite3' not in s and "game.db'" not in s
print('[PASS] deep audit targets, workloads, and no-DB contract')
