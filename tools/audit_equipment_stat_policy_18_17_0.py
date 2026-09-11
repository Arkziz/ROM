#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,hashlib,json,sqlite3,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
DB=R/"game.db"; P=R/"data/equipment_profiles.py"; G=R/"db_modules/generated_equipment.py"; D=R/"systems/dynamic_equipment_system.py"; C=R/"data/stat_system_config.py"
REPORT=R/"reports/stage_18_17_0_equipment_stat_policy_audit.json"; MD=R/"MD/STAGE_18_17_0_EQUIPMENT_STAT_POLICY_AUDIT.md"
CLASSES=("warrior","knight","scout","rogue","mage","priest")
EXPECTED={"warrior":{"rank":["str","dex"],"allowed":["str","dex","sta"]},"knight":{"rank":["str","dex"],"allowed":["str","dex","sta"]},"scout":{"rank":["str","dex"],"allowed":["str","dex","sta"]},"rogue":{"rank":["dex","str"],"allowed":["dex","str","sta"]},"mage":{"rank":["int","wis"],"allowed":["int","wis","sta"]},"priest":{"rank":["int","wis"],"allowed":["int","wis","sta"]}}
def text(p):return p.read_text(encoding="utf-8-sig")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def literal(p,name):
 t=ast.parse(text(p)); found=[]
 for n in t.body:
  if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets):found.append(ast.literal_eval(n.value))
 if len(found)!=1:raise RuntimeError(f"{p.name}:{name} definitions={len(found)}")
 return found[0]
def funcs(p):return [n.name for n in ast.parse(text(p)).body if isinstance(n,ast.FunctionDef)]
def live_db():
 before=sha(DB); c=sqlite3.connect(DB.resolve().as_uri()+"?mode=ro",uri=True)
 try:
  c.execute("PRAGMA query_only=ON"); cols=[r[1] for r in c.execute("PRAGMA table_info(items)")]
  wanted=[x for x in ("id","name","type","category","slot","item_subtype","armor_type","rarity","level","bonus_str","bonus_dex","bonus_int","bonus_wis","bonus_sta","pdef","mdef") if x in cols]
  rows=[]
  if wanted:
   sql="SELECT "+",".join('"'+x+'"' for x in wanted)+" FROM items"
   for row in c.execute(sql):
    item=dict(zip(wanted,row)); typ=str(item.get("type") or item.get("category") or "").lower()
    if typ in ("equipment","weapon","armor","jewelry") or int(item.get("id") or 0)>=10000:rows.append(item)
  generated=[x for x in rows if int(x.get("id") or 0)>=10000]
  dist=Counter()
  for x in generated:
   stats=tuple(k for k in ("str","dex","int","wis","sta") if int(x.get("bonus_"+k) or 0)>0)
   dist[(str(x.get("slot")),str(x.get("item_subtype")),str(x.get("armor_type")),str(x.get("rarity")),stats)]+=1
  out={"quick_check":c.execute("PRAGMA quick_check").fetchone()[0],"foreign_key_violations":c.execute("PRAGMA foreign_key_check").fetchall(),"total_changes":c.total_changes,"item_columns":cols,"equipment_rows":len(rows),"generated_rows":len(generated),"generated_distribution":[{"slot":k[0],"subtype":k[1],"armor_type":k[2],"rarity":k[3],"stats":list(k[4]),"count":v} for k,v in sorted(dist.items(),key=lambda z:(-z[1],z[0]))]}
 finally:c.close()
 out.update(sha256_before=before,sha256_after=sha(DB));out["unchanged"]=out["sha256_before"]==out["sha256_after"];return out
def main():
 for p in (P,G,D,C,DB):
  if not p.exists():raise RuntimeError(f"missing {p.relative_to(R)}")
 for p in (P,G,D,C):ast.parse(text(p))
 main=literal(P,"MAIN_HAND_PROFILES");off=literal(P,"OFF_HAND_PROFILES");slot=literal(P,"ARMOR_EXTRA_STATS_BY_SLOT");armor_allowed=literal(P,"ARMOR_ALLOWED_BY_CLASS");main_allowed=literal(P,"MAIN_HAND_ALLOWED_BY_CLASS");off_allowed=literal(P,"OFF_HAND_ALLOWED_BY_CLASS");armor=literal(G,"ARMOR_PRIMARY_STAT_PROFILES");defense=literal(G,"ARMOR_DEFENSE_DISTRIBUTION_PROFILES")
 issues=[];matrix={};shared=defaultdict(list)
 for cls,atype in armor_allowed.items():shared[atype].append(cls)
 for cls in CLASSES:
  allowed=set(EXPECTED[cls]["allowed"]);atype=armor_allowed.get(cls);ap=armor.get(atype,{})
  astats={s for s,_ in ap.get("primary_weights",[])}|{s for s,_ in ap.get("secondary_weights",[])}
  row={"armor_type":atype,"expected":EXPECTED[cls],"armor_stats":sorted(astats),"main_hand":[],"off_hand":[]}
  if astats-allowed or set(EXPECTED[cls]["rank"])-astats:issues.append({"severity":"HIGH","class":cls,"kind":"armor","unwanted":sorted(astats-allowed),"missing":sorted(set(EXPECTED[cls]["rank"])-astats)})
  for sub in main_allowed.get(cls,[]):
   actual=set(main.get(sub,{}).get("main_stats",[]))|set(main.get(sub,{}).get("extra_stats",[]));item={"subtype":sub,"stats":sorted(actual),"unwanted":sorted(actual-allowed),"missing":sorted(set(EXPECTED[cls]["rank"])-actual)};row["main_hand"].append(item)
   if item["unwanted"] or item["missing"]:issues.append({"severity":"HIGH","class":cls,"kind":"main_hand",**item})
  for sub in off_allowed.get(cls,[]):
   actual=set(off.get(sub,{}).get("main_stats",[]))|set(off.get(sub,{}).get("extra_stats",[]));item={"subtype":sub,"stats":sorted(actual),"unwanted":sorted(actual-allowed),"missing":sorted(set(EXPECTED[cls]["rank"])-actual)};row["off_hand"].append(item)
   if item["unwanted"]:issues.append({"severity":"MEDIUM","class":cls,"kind":"off_hand",**item})
  for jewelry in ("necklace","ring"):
   pool=set(slot.get(jewelry,[]));unwanted=sorted(pool-allowed);missing=sorted(set(EXPECTED[cls]["rank"])-pool)
   if unwanted or missing:issues.append({"severity":"HIGH","class":cls,"kind":"jewelry","slot":jewelry,"pool":sorted(pool),"unwanted":unwanted,"missing":missing})
  matrix[cls]=row
 for atype,classes in shared.items():
  if len(classes)>1 and len({tuple(EXPECTED[c]["rank"]) for c in classes})>1:issues.append({"severity":"HIGH","kind":"shared_armor_profile","armor_type":atype,"classes":classes})
 db=live_db();duplicate=sorted(set(funcs(G))&set(funcs(D)))
 report={"stage":"18.17.0","status":"PASS","generated_at_utc":datetime.now(timezone.utc).isoformat(),"read_only":True,"production_mutation":False,"sources":{"profiles":"data/equipment_profiles.py","generator":"db_modules/generated_equipment.py","dynamic_compat":"systems/dynamic_equipment_system.py","stat_config":"data/stat_system_config.py"},"expected_class_stats":EXPECTED,"armor_allowed_by_class":armor_allowed,"main_hand_allowed_by_class":main_allowed,"off_hand_allowed_by_class":off_allowed,"armor_defense_profiles":defense,"armor_primary_profiles":armor,"main_hand_profiles":main,"off_hand_profiles":off,"slot_extra_stat_pools":slot,"class_matrix":matrix,"shared_armor_profiles":dict(shared),"issues":issues,"issue_counts":dict(Counter(x["severity"] for x in issues)),"duplicate_functions_generator_vs_dynamic_compat":duplicate,"database":db,"recommendations":{"canonical_policy_module":"data/equipment_stat_policy.py","generator_owner":"db_modules/generated_equipment.py","target_contract":"target_class + slot + subtype + armor_type + rarity + level","defense_policy":"preserve cloth/leather/chain/plate PDEF/MDEF identity","existing_generated_items":"do not rewrite automatically; apply the new policy only to newly generated items unless a separate migration is approved","principles":["pass normalized target_class into stat generation","split Mage/Priest and Scout/Rogue primary-stat weights","build necklace/ring pools from target_class","preserve rarity multipliers and subtype identity initially","add deterministic fixtures for all six classes"]},"approximate_plan":["18.17.1 canonical class-aware policy and validator","18.17.2 integrate target_class into new generated equipment","18.17.3 deterministic class/slot/subtype/rarity regressions","18.17.4 static catalog and shop/loot/preview/comparison parity","18.17.5 manual acceptance and closure"]}
 if db["quick_check"]!="ok" or db["foreign_key_violations"] or db["total_changes"] or not db["unchanged"]:report["status"]="FAIL"
 REPORT.parent.mkdir(exist_ok=True);MD.parent.mkdir(exist_ok=True);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
 lines=["# Stage 18.17.0: Equipment Stat Policy Read-only Audit","",f"**Status:** {report['status']}","**Production mutation:** none","","## Findings","",f"- Total findings: **{len(issues)}**.",f"- Severity: `{report['issue_counts']}`.","- Armor class restrictions and PDEF/MDEF identity are already present.","- Primary-stat generation remains partly armor-type, slot and subtype based rather than target-class based.","- Shared cloth and leather profiles do not distinguish Mage/Priest and Scout/Rogue.","- Necklace and ring pools are not class-aware.","- Existing generated items should not be rewritten automatically.","","## Approximate plan",""]
 for i,x in enumerate(report["approximate_plan"],1):lines.append(f"{i}. {x}.")
 lines += ["","## Database safety","",f"- quick_check: `{db['quick_check']}`.",f"- FK violations: `{len(db['foreign_key_violations'])}`.",f"- DB unchanged: `{db['unchanged']}`.",f"- Generated rows inspected: `{db['generated_rows']}`."]
 MD.write_text("\n".join(lines)+"\n",encoding="utf-8")
 if report["status"]!="PASS":raise RuntimeError("read-only audit invariant failed")
 print(json.dumps({"status":"PASS","findings":len(issues),"severity":report["issue_counts"],"generated_rows":db["generated_rows"],"db_unchanged":db["unchanged"],"json":str(REPORT.relative_to(R)),"md":str(MD.relative_to(R))},ensure_ascii=False))
if __name__=="__main__":main()
