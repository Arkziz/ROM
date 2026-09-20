#!/usr/bin/env python3
from __future__ import annotations
import ast,hashlib,json,re,sqlite3,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
OUT=R/"reports"/"simulation"/"stage_18_30_5a_canonical_character_creation_and_player_stats_audit.json"
CLASSES=("warrior","knight","scout","rogue","mage","priest")
FILES=("data/player_hp.py","systems/stat_system.py","systems/character_system.py","db_modules/character.py","db_modules/user.py","systems/simulation/combat_actor_stats.py","systems/simulation/progression_provider.py")
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def source(rel):
 p=R/rel;return p.read_text(encoding="utf-8") if p.is_file() else ""
def funcs(rel):
 s=source(rel)
 if not s:return []
 tree=ast.parse(s);return sorted(n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))
def constants(rel,names):
 s=source(rel);tree=ast.parse(s) if s else ast.Module(body=[],type_ignores=[]);out={}
 for n in tree.body:
  if isinstance(n,(ast.Assign,ast.AnnAssign)):
   targets=n.targets if isinstance(n,ast.Assign) else [n.target]
   for t in targets:
    if isinstance(t,ast.Name) and t.id in names:
     try:out[t.id]=ast.literal_eval(n.value)
     except Exception:out[t.id]=ast.unparse(n.value)
 return out
def calls(rel,name):
 s=source(rel)
 if not s:return []
 tree=ast.parse(s);rows=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Call):
   fn=ast.unparse(n.func)
   if name in fn:rows.append({"call":fn,"line":n.lineno,"args":[ast.unparse(x) for x in n.args],"keywords":{x.arg:ast.unparse(x.value) for x in n.keywords}})
 return rows
def db_contract():
 db=(R/"game.db").resolve();con=sqlite3.connect(f"file:{db.as_posix()}?mode=ro",uri=True)
 try:
  cols=[{"name":r[1],"type":r[2],"notnull":bool(r[3]),"default":r[4],"pk":bool(r[5])} for r in con.execute("PRAGMA table_info(users)")]
  row=con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
  count=con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
  return {"users_columns":cols,"users_create_sql":row[0] if row else None,"existing_user_count":count}
 finally:con.close()
def main():
 from data.player_hp import calculate_base_max_hp,get_starting_max_hp
 from systems.simulation.combat_actor_stats import build_combat_stat_snapshot
 from systems.simulation.models import SimulationEquipment,SimulationInventory
 production_start=int(get_starting_max_hp());assert production_start==130,production_start
 matrix=[]
 for cls in CLASSES:
  for level in (1,2,5,10):
   snap=build_combat_stat_snapshot(cls,level,SimulationInventory(),SimulationEquipment())
   canonical_hp=int(calculate_base_max_hp(level,snap.sta))
   matrix.append({"class":cls,"level":level,"sta":snap.sta,"canonical_base_max_hp":canonical_hp,"simulation_max_hp":snap.max_hp,"delta":snap.max_hp-canonical_hp,"parity":"PASS" if snap.max_hp==canonical_hp else "FAIL"})
 char=source("systems/character_system.py");dbchar=source("db_modules/character.py");user=source("db_modules/user.py");sim=source("systems/simulation/combat_actor_stats.py")
 findings=[]
 if any(x["parity"]=="FAIL" for x in matrix):findings.append("SIMULATION_MAX_HP_PARITY_FAILURE")
 if "calculate_base_max_hp" not in sim:findings.append("SIMULATION_DOES_NOT_USE_CANONICAL_PLAYER_HP_OWNER")
 creation_hits=[]
 for rel,text in (("systems/character_system.py",char),("db_modules/character.py",dbchar),("db_modules/user.py",user)):
  for pat in (r"INSERT\s+INTO\s+users",r"UPDATE\s+users\s+SET\s+character_class",r"refresh_user_mp",r"get_starting_max_hp",r"calculate_base_max_hp"):
   for m in re.finditer(pat,text,re.I):creation_hits.append({"file":rel,"pattern":pat,"line":text[:m.start()].count("\n")+1})
 payload={
  "stage":"18.30.5a","verdict":"FAIL" if findings else "PASS","mode":"read-only",
  "canonical_starting_hp":{"owner":"data.player_hp","function":"get_starting_max_hp","value":production_start,"formula":{"STARTING_HP_BASE":60,"HP_PER_LEVEL":20,"HP_PER_STAMINA":5,"DEFAULT_STARTING_LEVEL":1,"DEFAULT_STARTING_STAMINA":10}},
  "canonical_player_hp_constants":constants("data/player_hp.py",{"STARTING_HP_BASE","HP_PER_LEVEL","HP_PER_STAMINA","DEFAULT_STARTING_LEVEL","DEFAULT_STARTING_STAMINA"}),
  "character_creation_and_class_selection_hits":creation_hits,
  "functions":{"data/player_hp.py":funcs("data/player_hp.py"),"systems/character_system.py":funcs("systems/character_system.py"),"db_modules/character.py":funcs("db_modules/character.py"),"db_modules/user.py":funcs("db_modules/user.py"),"systems/simulation/combat_actor_stats.py":funcs("systems/simulation/combat_actor_stats.py")},
  "canonical_hp_calls":{rel:calls(rel,"calculate_base_max_hp") for rel in FILES},
  "simulation_matrix":matrix,"findings":findings,
  "recommended_next_patch":"patch_18_30_5b_audit_canonical_player_stat_pipeline.py",
  "database_contract":db_contract(),"files_sha256":{rel:sha(R/rel) for rel in FILES if (R/rel).is_file()}
 }
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"[PASS] canonical starting HP: {production_start}")
 print(f"[INFO] simulation parity failures: {sum(x['parity']=='FAIL' for x in matrix)}")
 print(f"[INFO] findings: {', '.join(findings) if findings else 'none'}")
 print(f"[REPORT] {OUT.relative_to(R)}")
if __name__=="__main__":main()
