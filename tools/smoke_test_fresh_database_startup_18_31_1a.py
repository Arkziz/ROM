#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CODE="\n".join([
 "import json",
 "from db_modules.connection import conn, init_db",
 "from systems.fresh_database_bootstrap import run_fresh_database_schema_bootstrap",
 "from migrations.runner import run_pending_migrations",
 "init_db()",
 "bootstrap=run_fresh_database_schema_bootstrap()",
 "result=run_pending_migrations(conn)",
 "rows={r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type=\'table\'\").fetchall()}",
 "items=[tuple(r) for r in conn.execute(\"SELECT id,type,category,max_stack FROM items WHERE id IN (501,504) ORDER BY id\").fetchall()]",
 "applied=[r[0] for r in conn.execute(\"SELECT migration_name FROM schema_migrations ORDER BY migration_name\").fetchall()]",
 "quick=[r[0] for r in conn.execute(\"PRAGMA quick_check\").fetchall()]",
 "foreign=[tuple(r) for r in conn.execute(\"PRAGMA foreign_key_check\").fetchall()]",
 "print(json.dumps({\"bootstrap\":bootstrap,\"migration\":result,\"tables\":sorted(rows),\"items\":items,\"applied\":applied,\"quick\":quick,\"foreign\":foreign},ensure_ascii=False,default=str))",
])
def run_cycle(work):
 env=dict(os.environ);env["PYTHONPATH"]=str(ROOT)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
 p=subprocess.run([sys.executable,"-c",CODE],cwd=work,text=True,capture_output=True,env=env,timeout=300)
 if p.returncode:raise RuntimeError(p.stdout+"\n"+p.stderr)
 return json.loads(p.stdout.strip().splitlines()[-1])
def validate(data,label):
 assert "location_travels" in data["tables"],(label,"location_travels missing")
 assert [row[0] for row in data["items"]]==[501,504],(label,data["items"])
 for name in ("045a_seed_new_path_sphere_dependency.py","046_sphere_consumable_presentation.py","047_sphere_stack_and_category_fix.py","048_rebirth_sphere_stack_limit.py","049_persistent_location_travel.py","050_event_kill_statistics.py","051_event_shop_exchange.py"):assert name in data["applied"],(label,name)
 assert data["quick"]==["ok"] and data["foreign"]==[]
with tempfile.TemporaryDirectory(prefix="rom_fresh_startup_18_31_1a_") as td:
 work=Path(td);first=run_cycle(work);validate(first,"first");second=run_cycle(work);validate(second,"second")
 assert second["migration"]["applied"]==[],second["migration"]
 assert "045a_seed_new_path_sphere_dependency.py" in second["migration"]["skipped"]
 print("[PASS] fresh DB migrations 000-051, sphere dependencies, travel table, and second-start idempotency")
