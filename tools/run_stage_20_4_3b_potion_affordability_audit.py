#!/usr/bin/env python3
from __future__ import annotations
import json,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.world_progression import WorldProgressionSimulator
CLASSES=("warrior","knight","scout","rogue","mage","priest")
SEEDS=(20430501,20430502,20430503)
TARGET_LEVEL=5

def event_dict(e):return {"event_type":e.event_type,"details":dict(e.details)}
def run_one(cls,seed):
 sim=WorldProgressionSimulator(ROOT,cls,TARGET_LEVEL,"regular",seed,max_days=365)
 result=sim.run();events=[event_dict(e) for e in result.events]
 final=next((e["details"] for e in reversed(events) if e["event_type"]=="simulation_final_state"),{})
 pot=dict(final.get("potion_affordability") or {})
 repair=round(sum(float(e["details"].get("repair_cost",0) or 0) for e in events if e["event_type"]=="city_visit"),2)
 potion=float(pot.get("total_potion_spend",0) or 0);mob=float(result.gold_gained);after=max(0.0,mob-repair)
 ratio=lambda n,d:None if d<=0 else round(n/d,6)
 return {"class":cls,"seed":seed,"status":result.status,"final_level":result.final_level,"days":result.days,"battles":result.battles,"wins":result.wins,"deaths":result.deaths,"mob_gold":round(mob,2),"final_gold":round(float(result.final_gold),2),"hp_spend":float(pot.get("hp_spend",0) or 0),"mp_spend":float(pot.get("mp_spend",0) or 0),"potion_spend":round(potion,2),"repair_spend":repair,"mandatory_spend":round(potion+repair,2),"potion_to_mob_gold_ratio":ratio(potion,mob),"potion_to_after_repair_ratio":ratio(potion,after),"mandatory_to_mob_gold_ratio":ratio(potion+repair,mob),"bought":pot.get("bought",{}),"used_free_or_dropped":pot.get("used_free_or_dropped",{})}
def score(row):
 value=row.get("mandatory_to_mob_gold_ratio");return -1.0 if value is None else float(value)
def main(out_path):
 runs=[run_one(cls,seed) for cls in CLASSES for seed in SEEDS]
 if any(r["status"]!="completed" or r["final_level"]<TARGET_LEVEL for r in runs):raise RuntimeError('Not all simulations reached level 5')
 classes={}
 for cls in CLASSES:
  rows=sorted([r for r in runs if r["class"]==cls],key=score)
  classes[cls]={"typical":rows[1],"poor_luck":rows[-1],"all_seeds":rows}
 typical=[v["typical"] for v in classes.values()];poor=[v["poor_luck"] for v in classes.values()]
 def aggregate(rows):
  ratios=[score(r) for r in rows];return {"total_potion_spend":round(sum(r["potion_spend"] for r in rows),2),"total_repair_spend":round(sum(r["repair_spend"] for r in rows),2),"median_mandatory_to_mob_gold_ratio":round(statistics.median(ratios),6),"max_mandatory_to_mob_gold_ratio":round(max(ratios),6),"classes_with_hp_purchases":sum(r["hp_spend"]>0 for r in rows),"mana_classes_with_mp_purchases":sum(r["class"] in {"mage","priest"} and r["mp_spend"]>0 for r in rows)}
 payload={"schema_version":"20.4.3b.v1","generated_at":datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),"target_level":TARGET_LEVEL,"profile":"regular","seeds":list(SEEDS),"runs":runs,"class_scenarios":classes,"typical_aggregate":aggregate(typical),"poor_luck_aggregate":aggregate(poor)}
 Path(out_path).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('[OK] Stage 20.4.3b simulations - 6 classes x 3 seeds through level 5')
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: audit.py OUTPUT_JSON')
 main(sys.argv[1])
