#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"main.py"; t=ast.parse(p.read_text(encoding="utf-8-sig"))
def name(n):
 return n.id if isinstance(n,ast.Name) else ((name(n.value)+"."+n.attr).strip(".") if isinstance(n,ast.Attribute) else "")
c=[(name(n.func),n.lineno) for n in ast.walk(t) if isinstance(n,ast.Call)]
def one(s):
 x=[ln for n,ln in c if n.endswith(s)]; assert len(x)==1,(s,x); return x[0]
defs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=="_validate_startup_migration_result"]; assert len(defs)==1
m=one("run_pending_migrations"); maint=one("run_db_startup_maintenance"); nw=one("start_notification_worker"); pw=one("start_pve_auto_escape_worker"); tw=one("start_travel_worker"); poll=one("run_bot_polling_resilient"); assert m<maint<nw<pw<tw<poll,(m,maint,nw,pw,tw,poll)
source=p.read_text(encoding="utf-8-sig"); assert "DB migrations skipped/error" not in source; assert "ROM startup aborted by database migration gate" in source
print("PASS: Stage 21.2.2 deterministic startup migration gate")
