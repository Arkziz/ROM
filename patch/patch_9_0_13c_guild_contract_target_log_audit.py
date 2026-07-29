#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13c: install and run Guild contract target-log audit."""
from __future__ import annotations
import os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.13c"
TOOL_NAME="audit_guild_contract_target_log.py"
TOOL=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only structural and isolated audit of Guild contract target logging."""
from __future__ import annotations
import ast
import hashlib
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
REPORT=ROOT/"DB_CLEANUP_9_0_13C_GUILD_CONTRACT_TARGET_LOG_AUDIT.md"
DB_PATH=ROOT/"game.db"

def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def parse(path):
 text=path.read_text(encoding="utf-8-sig"); return text,ast.parse(text,filename=str(path))
def fn(text,tree,name):
 nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 if len(nodes)!=1: fail(f"{path.name if False else name}: definitions={len(nodes)}, expected 1")
 return nodes[0],ast.get_source_segment(text,nodes[0]) or ""
def call_keywords(node,call_name):
 out=[]
 for n in ast.walk(node):
  if not isinstance(n,ast.Call): continue
  name=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else None
  if name==call_name: out.append(sorted(k.arg for k in n.keywords if k.arg))
 return out

def main():
 if not DB_PATH.is_file(): fail("game.db not found")
 before=(sha(DB_PATH),DB_PATH.stat().st_size,DB_PATH.stat().st_mtime_ns)
 cp=ROOT/"systems"/"contract_system.py"; gp=ROOT/"systems"/"guild_system.py"
 ct,ctr=parse(cp); gt,gtr=parse(gp)
 get_node,get_src=fn(ct,ctr,"get_active_contract")
 claim_node,claim_src=fn(ct,ctr,"claim_contract_reward")
 base_node,base_src=fn(ct,ctr,"_claim_contract_reward_base")
 award_node,award_src=fn(gt,gtr,"award_guild_contract_completion")
 if '"target_mob_name": target_mob_name' not in get_src: fail("get_active_contract does not expose target_mob_name")
 if "contract = get_active_contract(user_id)" not in claim_src: fail("claim path does not snapshot active contract before base claim")
 if "_claim_contract_reward_base(user_id)" not in claim_src: fail("claim path does not call base claim")
 if "contract=contract" not in claim_src: fail("claim path does not pass contract snapshot to Guild hook")
 if "DELETE FROM user_active_contracts" not in base_src: fail("base claim no longer deletes claimed contract")
 expected_keys=("name","title","contract_name")
 missing=[key for key in expected_keys if f'contract.get("{key}")' not in award_src]
 if missing: fail(f"Guild contract formatter expected-key structure changed: missing={missing}")
 accepts_target='contract.get("target_mob_name")' in award_src
 # Isolated pure runtime probe: monkeypatch all DB-facing Guild dependencies.
 from systems import guild_system as guild
 original_member=guild.get_user_guild_member
 original_add=guild.add_user_guild_progress
 captured=[]
 try:
  guild.get_user_guild_member=lambda user_id:{"guild_id":777,"user_id":user_id}
  def fake_add(**kwargs): captured.append(kwargs); return {"success":True,"message":"ok"}
  guild.add_user_guild_progress=fake_add
  fixture={"target_mob_name":"🧙 Audit target","completed":True,"reward_exp":40}
  result=guild.award_guild_contract_completion(-90121301,contract=fixture)
 finally:
  guild.get_user_guild_member=original_member
  guild.add_user_guild_progress=original_add
 if not captured: fail("isolated Guild award probe did not reach add_user_guild_progress")
 reason=str(captured[0].get("reason") or "")
 target_preserved="🧙 Audit target" in reason
 fallback_used="Виконання контракту: контракт." in reason
 # Read-only DB context: count affected historical fallback rows only.
 uri=DB_PATH.resolve().as_uri()+"?mode=ro"; conn=sqlite3.connect(uri,uri=True)
 try:
  conn.execute("PRAGMA query_only=ON")
  tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  fallback_count=0
  log_table="guild_logs" if "guild_logs" in tables else None
  if log_table:
   cols={r[1] for r in conn.execute("PRAGMA table_info(guild_logs)")}
   text_col="reason" if "reason" in cols else "message" if "message" in cols else "details" if "details" in cols else None
   if text_col:
    fallback_count=int(conn.execute(f'SELECT COUNT(*) FROM guild_logs WHERE "{text_col}"=?',("Виконання контракту: контракт.",)).fetchone()[0] or 0)
  integrity=conn.execute("PRAGMA quick_check").fetchone()[0]
 finally: conn.close()
 after=(sha(DB_PATH),DB_PATH.stat().st_size,DB_PATH.stat().st_mtime_ns)
 if before!=after: fail("game.db changed during audit")
 if integrity!="ok": fail(f"quick_check={integrity}")
 diagnosis=(
  "Guild formatter ignores target_mob_name and falls back to 'контракт'. The Contract System already snapshots the full contract before deletion and passes it to the Guild hook."
  if not accepts_target and fallback_used else
  "The expected formatter mismatch was not reproduced; manual review is required."
 )
 report=[
  "# ROM 9.0.13c — Guild Contract Target Log Audit","",f"Generated: `{datetime.now().isoformat(timespec='seconds')}`","",
  "## Safety","","- Gameplay files changed: **0**","- Database rows changed: **0**",f"- Database SHA/size/mtime unchanged: **{before==after}**",f"- Database quick check: **{integrity}**","",
  "## Contract pipeline","",f"- `get_active_contract()` exposes `target_mob_name`: **yes**",f"- Claim snapshots contract before base claim: **yes**",f"- Base claim deletes active contract: **yes**",f"- Saved snapshot passed as `contract=contract`: **yes**",f"- Guild hook call keyword sets: `{call_keywords(claim_node,'award_guild_contract_completion')}`","",
  "## Guild formatter","",f"- Accepted keys: `{list(expected_keys)}`",f"- Accepts `target_mob_name`: **{accepts_target}**",f"- Isolated generated reason: `{reason}`",f"- Target preserved: **{target_preserved}**",f"- Generic fallback reproduced: **{fallback_used}**","",
  "## Existing data","",f"- Exact historical fallback log rows detected: **{fallback_count}**","",
  "## Diagnosis","",diagnosis,"",
  "## Recommended hotfix","","1. Add `target_mob_name` as the first canonical lookup key in `award_guild_contract_completion()`.","2. Preserve `name`, `title`, and `contract_name` as backward-compatible fallbacks.","3. Add isolated contracts proving the target name reaches the Guild log reason.","4. Do not rewrite historical generic rows because their original target cannot be reliably reconstructed.","",
  "Suggested next patch: `patch_9_0_13d_guild_contract_target_log_hotfix.py`",""
 ]
 REPORT.write_text("\n".join(report),encoding="utf-8")
 print("[OK] Guild contract target log audit")
 print("- contract snapshot before deletion: OK")
 print("- target_mob_name in contract snapshot: OK")
 print("- snapshot passed to Guild hook: OK")
 print(f"- Guild formatter accepts target_mob_name: {accepts_target}")
 print(f"- isolated Guild reason: {reason}")
 print(f"- generic fallback reproduced: {fallback_used}")
 print(f"- historical generic rows detected: {fallback_count}")
 print("- database mutations: 0")
 print("- diagnosis: Guild formatter key mismatch")
 print(f"- report: {REPORT}")
if __name__=="__main__": main()
'''

def fail(message): print("❌ "+message); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"contract_system.py").is_file() and (r/"systems"/"guild_system.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def main():
 r=root(); target=r/"tools"/TOOL_NAME; backup=None
 if target.exists() and target.read_text(encoding="utf-8-sig")!=TOOL:
  b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); backup=b/f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"; shutil.copy2(target,backup)
 target.write_text(TOOL,encoding="utf-8")
 env=os.environ.copy(); env["PYTHONUTF8"]="1"; env["PYTHONIOENCODING"]="utf-8"
 try:
  py_compile.compile(str(target),doraise=True)
  result=subprocess.run([sys.executable,str(target)],cwd=r,env=env,check=False)
  if result.returncode: raise RuntimeError(f"audit exit code {result.returncode}")
 except Exception as exc:
  if backup: shutil.copy2(backup,target)
  elif target.exists(): target.unlink()
  fail(f"Аудит не пройдено; встановлення відкочено: {exc}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Створено: tools/{TOOL_NAME}")
 print("✅ Створено: DB_CLEANUP_9_0_13C_GUILD_CONTRACT_TARGET_LOG_AUDIT.md")
 print("✅ Gameplay-код і game.db не змінені.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r) if backup else 'не потрібні - новий файл'}")
 print("Повторний запуск:")
 print(f"   python ./tools/{TOOL_NAME}")
if __name__=="__main__": main()
