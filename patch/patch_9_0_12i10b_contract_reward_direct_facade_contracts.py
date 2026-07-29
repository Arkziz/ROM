#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i10b: switch Contract Reward public API to direct facade and add isolated contracts."""
from __future__ import annotations
import ast, os, py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i10b"
CAPTURE="_base_claim_contract_reward_before_guild_reward_v1"
TEST_NAME="smoke_test_contract_reward_direct_facade.py"
AUDIT_NAME="audit_contract_reward_dependency.py"
TESTS=(TEST_NAME,"smoke_test_contract_contracts.py","smoke_test_rom_core.py","check_imports.py")
FACADE='''def claim_contract_reward(user_id):
    """Public Contract Reward facade backed by systems.contract_system."""
    from systems.contract_system import claim_contract_reward as _func
    return _func(user_id)
'''
TEST=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated mutation contracts for direct Contract Reward facade."""
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db
from systems import contract_system as contract

IDS=(-90121011,-90121012,-90121013)
CAPTURE="_base_claim_contract_reward_before_guild_reward_v1"

def fail(x): print("[FAIL] "+x); raise SystemExit(1)
def cols(table): return [r[1] for r in db.conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
def user_tables():
 out=[]
 for (name,) in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
  try:
   if "user_id" in cols(name): out.append(name)
  except Exception: pass
 return out
def cleanup():
 for table in [x for x in user_tables() if x!="users"]:
  for uid in IDS:
   try: db.conn.execute(f'DELETE FROM "{table}" WHERE user_id=?',(uid,))
   except Exception: pass
 for uid in IDS:
  try: db.conn.execute("DELETE FROM users WHERE user_id=?",(uid,))
  except Exception: pass
 db.conn.commit()
def real_snapshot():
 c=cols("users"); q=",".join(f'"{x}"' for x in c)
 return c,[tuple(r) for r in db.conn.execute(f'SELECT {q} FROM users WHERE user_id>=0 ORDER BY user_id').fetchall()]
def create_fixture(uid,completed,current=0,reward=40):
 db.create_user(uid)
 db.init_contract_system()
 db.conn.execute("UPDATE users SET level=5,exp=0,daily_contracts_completed=0,daily_contract_date=? WHERE user_id=?",(db.get_today_str(),uid))
 db.conn.execute("""INSERT INTO user_active_contracts
 (user_id,created_date,player_level,target_mob_name,target_mob_level,target_min_level,target_max_level,target_kills,current_kills,reward_exp,completed,reward_claimed)
 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
 (uid,db.get_today_str(),5,"fixture_target",5,1,10,5,current,reward,completed,0))
 db.conn.commit()
def state(uid):
 user=db.conn.execute("SELECT level,exp,daily_contracts_completed FROM users WHERE user_id=?",(uid,)).fetchone()
 count=db.conn.execute("SELECT COUNT(*) FROM user_active_contracts WHERE user_id=?",(uid,)).fetchone()[0]
 return tuple(user),int(count)
def main():
 source=(ROOT/"db.py").read_text(encoding="utf-8-sig"); tree=ast.parse(source); defs=[]
 for n in tree.body:
  if isinstance(n,ast.FunctionDef) and n.name=="claim_contract_reward": defs.append(n)
 if len(defs)!=2: fail(f"claim_contract_reward definitions={len(defs)}, expected 2 during i10b")
 final=ast.get_source_segment(source,defs[-1]) or ""
 if "systems.contract_system" not in final or CAPTURE in final: fail("final db claim is not direct facade")
 base=getattr(db,CAPTURE,None)
 if not callable(base): fail("base capture is not callable during equivalence stage")
 before=real_snapshot(); cleanup(); checks=0
 original_award=db.award_guild_contract_completion
 original_text=db.get_guild_activity_reward_text
 guild_calls=[]
 try:
  # Missing contract equivalence.
  if db.claim_contract_reward(IDS[0])!=base(IDS[0]): fail("missing-contract public/base mismatch")
  checks+=1
  # Incomplete contract equivalence and no mutation.
  create_fixture(IDS[0],0,current=2,reward=40); pre=state(IDS[0])
  public=db.claim_contract_reward(IDS[0]); post=state(IDS[0])
  if public.get("success") is not False or pre!=post: fail(f"incomplete contract changed state: {pre}->{post}, result={public}")
  checks+=1
  # Completed base and direct-facade paths on equivalent fixtures.
  create_fixture(IDS[1],1,current=5,reward=40); create_fixture(IDS[2],1,current=5,reward=40)
  base_result=base(IDS[1]); base_state=state(IDS[1])
  def fake_award(user_id,contract=None):
   guild_calls.append((user_id,contract)); return {"success":True,"exp":50,"resource":3,"contracts":1}
  def fake_text(result): return "🏰 Fixture Guild reward"
  db.award_guild_contract_completion=fake_award
  db.get_guild_activity_reward_text=fake_text
  direct_result=db.claim_contract_reward(IDS[2]); direct_state=state(IDS[2])
  if base_state!=direct_state: fail(f"completed state mismatch: base={base_state}, direct={direct_state}")
  for result in (base_result,direct_result):
   if result.get("success") is not True or int(result.get("reward_exp",0))!=40: fail(f"completed result contract failed: {result}")
  if len(guild_calls)!=1 or guild_calls[0][0]!=IDS[2]: fail(f"Guild hook calls invalid: {guild_calls}")
  if "Fixture Guild reward" not in str(direct_result.get("message") or ""): fail("Guild reward text not appended")
  if direct_state[0][2]!=1 or direct_state[1]!=0: fail(f"completed contract counters invalid: {direct_state}")
  checks+=5
  # Repeat claim must not reward again.
  before_repeat=state(IDS[2]); repeat=db.claim_contract_reward(IDS[2]); after_repeat=state(IDS[2])
  if repeat.get("success") is not False or before_repeat!=after_repeat or len(guild_calls)!=1: fail("repeat reward protection failed")
  checks+=1
 finally:
  db.award_guild_contract_completion=original_award
  db.get_guild_activity_reward_text=original_text
  cleanup()
 if before!=real_snapshot(): fail("real users changed")
 print("[OK] contract reward direct facade isolated contracts")
 print(f"- contract checks: {checks}")
 print("- missing/incomplete paths: OK")
 print("- base/direct completed-state equivalence: OK")
 print("- EXP and daily completion: OK")
 print("- active contract deletion: OK")
 print("- Guild hook exactly once: OK")
 print("- repeat reward protection: OK")
 print("- fixture cleanup: OK")
 print("- real user mutations: 0")
if __name__=="__main__": main()
'''

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 h=Path(__file__).resolve()
 for r in (h.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"contract_system.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def fmap(tree):
 d={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): d.setdefault(n.name,[]).append(n)
 return d
def run(r,p,label):
 x=subprocess.run([sys.executable,str(p)],cwd=r)
 if x.returncode: raise RuntimeError(f"{label} exit code {x.returncode}")
def main():
 r=root(); dbp=r/"db.py"; tools=r/"tools"; testp=tools/TEST_NAME; auditp=tools/AUDIT_NAME; readiness=tools/"db_cleanup_readiness.py"
 for n in TESTS[1:]:
  if not (tools/n).is_file(): fail(f"Відсутній tools/{n}.")
 src=dbp.read_text(encoding="utf-8-sig"); tree=ast.parse(src); defs=fmap(tree); nodes=defs.get("claim_contract_reward",[])
 if len(nodes)!=2: fail(f"claim_contract_reward definitions={len(nodes)}, expected 2")
 final_src=ast.get_source_segment(src,nodes[-1]) or ""
 if "systems.contract_system" in final_src and CAPTURE not in final_src:
  print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
  for n in TESTS: run(r,tools/n,n)
  return
 if CAPTURE not in final_src: fail("Фінальний override не містить очікуваний capture")
 lines=src.splitlines(keepends=True); node=nodes[-1]; replacement=FACADE
 if lines[node.end_lineno-1].endswith("\n") and not replacement.endswith("\n"): replacement+="\n"
 lines[node.lineno-1:node.end_lineno]=[replacement]; updated="".join(lines)
 udefs=fmap(ast.parse(updated));
 if len(udefs.get("claim_contract_reward",[]))!=2: fail("Після facade switch змінено count definitions")
 retained=ast.get_source_segment(updated,udefs["claim_contract_reward"][-1]) or ""
 if "systems.contract_system" not in retained or CAPTURE in retained: fail("Direct facade validation failed")
 b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
 dbbak=b/f"db.py_{PATCH_ID}_direct_facade_{stamp}.bak"; shutil.copy2(dbp,dbbak)
 testbak=None
 if testp.exists(): testbak=b/f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"; shutil.copy2(testp,testbak)
 temp=dbp.with_name(".db.i10b.tmp")
 try:
  temp.write_text(updated,encoding="utf-8"); os.replace(temp,dbp); testp.write_text(TEST,encoding="utf-8")
  py_compile.compile(str(dbp),doraise=True); py_compile.compile(str(testp),doraise=True)
  for n in TESTS: run(r,tools/n,n)
  x=subprocess.run([sys.executable,str(readiness)],cwd=r,text=True,capture_output=True); print(x.stdout,end="")
  if x.returncode: raise RuntimeError(f"readiness exit code {x.returncode}")
  for expected in ("definitions: 351","duplicates: 1","legacy_refs: 0","unsafe_delete: 0","maybe_cleanup_later: 1"):
   if expected not in x.stdout: raise RuntimeError(f"readiness missing {expected}")
 except Exception as e:
  shutil.copy2(dbbak,dbp)
  if testbak: shutil.copy2(testbak,testp)
  elif testp.exists(): testp.unlink()
  if temp.exists(): temp.unlink()
  fail(f"Перевірка не пройдена; файли відновлено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print("✅ Фінальна db.claim_contract_reward переведена на direct Contract System facade.")
 print("✅ Ранню реалізацію та capture тимчасово збережено для i10c rollback/equivalence.")
 print("✅ Ізольовані mutation contracts пройдені.")
 print("Резервні копії:")
 print(f"   {dbbak.relative_to(r)}")
 if testbak: print(f"   {testbak.relative_to(r)}")
 print("Перевірки:")
 print(f"   python ./tools/{TEST_NAME}")
 for n in TESTS[1:]: print(f"   python ./tools/{n}")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
