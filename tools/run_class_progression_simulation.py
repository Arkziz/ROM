#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.class_progression import ClassProgressionRequest,run_class_progression

def main():
 p=argparse.ArgumentParser();p.add_argument("--class",dest="character_class",required=True,choices=("warrior","knight","scout","rogue","mage","priest"));p.add_argument("--target-level",type=int,required=True);p.add_argument("--seed",type=int,default=1);p.add_argument("--max-days",type=int,default=365);a=p.parse_args()
 print("[1/4] Запуск симуляції")
 payload=run_class_progression(ROOT,ClassProgressionRequest(a.character_class,a.target_level,a.seed,"hardcore",1,a.max_days,40))
 out=ROOT/"reports"/"simulation";out.mkdir(parents=True,exist_ok=True);stem=f"stage_18_30_progression_{a.character_class}_level_1_to_{a.target_level}_seed_{a.seed}";jp=out/(stem+".json");cp=out/(stem+"_loot.csv")
 jp.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
 with cp.open("w",encoding="utf-8-sig",newline="") as f:
  fields=("item_id","name","category","rarity","found","awarded","lost_due_capacity","destinations");w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in payload["loot_ledger"]:w.writerow({**row,"destinations":json.dumps(row["destinations"],ensure_ascii=False,sort_keys=True)})
 print("[2/4] Симуляцію завершено")
 print(f"[INFO] Рівень: 1 -> {payload['final_level']}; днів: {payload['time_to_target']['calendar_days']}; час: {payload['time_to_target']['formatted']}")
 e=payload["encounters"];o=payload["battle_outcomes"];print(f"[INFO] Зустрічі: normal {e['normal']}, elite {e['elite']}, boss {e['boss']}");print(f"[INFO] Результати: перемоги {o['victory']}, поразки {o['defeat']}, втечі {o['escape']}")
 print(f"[INFO] Лут знайдено: {payload['loot_found_total']}; позицій: {len(payload['loot_ledger'])}");print("[3/4] Повні звіти збережено");print(f"[REPORT] {jp.relative_to(ROOT)}");print(f"[REPORT] {cp.relative_to(ROOT)}");print("[4/4] PASS" if payload["target_reached"] else "[4/4] FAIL")
 return 0 if payload["target_reached"] else 2
if __name__=="__main__":raise SystemExit(main())
