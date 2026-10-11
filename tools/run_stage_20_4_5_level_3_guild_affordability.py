#!/usr/bin/env python3
from __future__ import annotations
import json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.world_progression import WorldProgressionSimulator
CLASSES=("warrior","knight","scout","rogue","mage","priest");SEEDS=(20450301,);COSTS=(100.0,75.0,50.0)
STORY_GOLD_TO_REACHED_LEVEL_3=7.0;LEVEL_UP_GOLD_TO_LEVEL_3=1.88;LEVEL_3_NORMAL_MOB_GOLD=0.215

def run_one(cls,seed):
 result=WorldProgressionSimulator(ROOT,cls,3,"regular",seed,max_days=365).run()
 final=round(float(result.final_gold)+STORY_GOLD_TO_REACHED_LEVEL_3+LEVEL_UP_GOLD_TO_LEVEL_3,2)
 rows={}
 for cost in COSTS:
  gap=max(0.0,cost-final);rows[str(int(cost))]={"affordable":final+1e-9>=cost,"gap":round(gap,2),"additional_level_3_normal_kills":0 if gap<=0 else int(-(-gap//LEVEL_3_NORMAL_MOB_GOLD))}
 return {"class":cls,"seed":seed,"status":result.status,"final_level":result.final_level,"simulator_net_wallet":round(float(result.final_gold),2),"story_gold_added":STORY_GOLD_TO_REACHED_LEVEL_3,"level_up_gold_added":LEVEL_UP_GOLD_TO_LEVEL_3,"effective_wallet_at_level_3":final,"candidates":rows}
def main(out):
 runs=[run_one(c,seed) for c in CLASSES for seed in SEEDS]
 if len(runs)!=6 or any(x["status"]!="completed" or x["final_level"]<3 for x in runs):raise RuntimeError('Incomplete level-3 simulation')
 classes={}
 for c in CLASSES:
  rows=[x for x in runs if x["class"]==c]
  if len(rows)!=1:raise RuntimeError(f'Expected one deterministic run for {c}, got {len(rows)}')
  classes[c]={"single_seed":rows[0],"all_seeds":rows}
 typical=[v["single_seed"] for v in classes.values()];poor=list(typical)
 candidates={}
 for cost in COSTS:
  key=str(int(cost));tk=[x["candidates"][key]["additional_level_3_normal_kills"] for x in typical];pk=[x["candidates"][key]["additional_level_3_normal_kills"] for x in poor]
  candidates[key]={"typical_classes_affording":sum(x["candidates"][key]["affordable"] for x in typical),"poor_classes_affording":sum(x["candidates"][key]["affordable"] for x in poor),"typical_median_extra_kills":statistics.median(tk),"typical_max_extra_kills":max(tk),"poor_median_extra_kills":statistics.median(pk),"poor_max_extra_kills":max(pk)}
 # Choose the highest tested price with typical median extra grind <=100 kills.
 eligible=[cost for cost in COSTS if candidates[str(int(cost))]["typical_median_extra_kills"]<=100]
 recommended=max(eligible) if eligible else min(COSTS)
 payload={"target_level":3,"classes":list(CLASSES),"seeds":list(SEEDS),"story_gold_added":7.0,"level_up_gold_added":1.88,"level_3_normal_mob_gold":0.215,"runs":runs,"class_scenarios":classes,"candidates":candidates,"recommended_cost":recommended,"policy":"highest candidate with typical median additional grind <=100 level-3 normal kills; otherwise 50"}
 Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('[OK] Stage 20.4.5 level-3 guild affordability - 6 classes x 1 seed')
if __name__=='__main__':main(sys.argv[1])
