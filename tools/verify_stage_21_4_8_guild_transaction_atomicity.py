#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"systems/guild_system.py"; tree=ast.parse(p.read_text(encoding="utf-8-sig"))
OWNERS=("archive_and_reset_guild_monthly_stats","cancel_guild_application","reject_guild_application","demote_guild_officer","recalculate_guild_level")
for name in OWNERS:
 owners=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]; assert len(owners)==1,(name,len(owners))
 fn=owners[0]; calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]
 assert sum(x.endswith("commit") for x in calls)==1,(name,calls); assert sum(x.endswith("rollback") for x in calls)==1,(name,calls)
 assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(x,ast.Raise) for x in ast.walk(h)) for h in ast.walk(fn)),name
for name in ("create_guild","kick_guild_member","leave_guild","transfer_guild_leadership","transfer_guild_leadership_and_leave"):
 matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
 if matches: assert any(isinstance(n,ast.Call) and ast.unparse(n.func).endswith("rollback") for n in ast.walk(matches[-1])),name
print("PASS: Stage 21.4.8 guild owner rollback invariants")
