#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.class_progression import ClassProgressionRequest,run_class_progression

def main():
 p=argparse.ArgumentParser();p.add_argument("--class",dest="character_class",required=True,choices=("warrior","knight","scout","rogue","mage","priest"));p.add_argument("--target-level",type=int,required=True);p.add_argument("--seed",type=int,default=1);p.add_argument("--max-days",type=int,default=365);a=p.parse_args();print("[1/4] Запуск симуляції")
 data=run_class_progression(ROOT,ClassProgressionRequest(a.character_class,a.target_level,a.seed,"hardcore",1,a.max_days,40));out=ROOT/"reports"/"simulation";out.mkdir(parents=True,exist_ok=True);stem=f"stage_18_30_progression_{a.character_class}_level_1_to_{a.target_level}_seed_{a.seed}";jp=out/(stem+".json");cp=out/(stem+"_loot.csv");ep=out/(stem+"_equipment.json")
 jp.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+chr(10),encoding="utf-8");ep.write_text(json.dumps({"class":data["class"],"level":data["final_level"],"final_loadout":data["final_loadout"]},ensure_ascii=False,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
 from systems.simulation.excel_reporting import write_consolidated_workbook
 xp=out/(stem+".xlsx")
 write_consolidated_workbook(data,xp)
 fields=("item_id","name_uk","name_raw","category","slot_uk","slot_key","item_level","armor_type_uk","armor_type","rarity_uk","rarity","found","equipped","sold","used_or_transformed","remaining","sale_gold")
 with cp.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in data["loot_lifecycle"]:w.writerow({key:row.get(key,"") for key in fields})
 print("[2/4] Симуляцію завершено");t=data["time_to_target"];print(f"[INFO] Рівень: 1 -> {data['final_level']}; календарних днів: {t['calendar_days']}; фактичний час: {t['hours']} год {t['minutes']} хв");e=data["encounters"];o=data["battle_outcomes"];m=data["mob_encounters"];print(f"[INFO] Зустрічі: normal {e['normal']}, elite {e['elite']}, boss {e['boss']}; унікальних мобів: {m['unique_mobs']}");print(f"[INFO] Різниця рівнів: -1={m['by_level_delta']['-1']}, 0={m['by_level_delta']['0']}, +1={m['by_level_delta']['1']}");print(f"[INFO] Перемоги {o['victory']}, поразки {o['defeat']}, втечі {o['escape']}");print(f"[INFO] Лут: {sum(x['found'] for x in data['loot_lifecycle'])}; екіпіровано: {sum(x['equipped'] for x in data['loot_lifecycle'])}; продано: {sum(x['sold'] for x in data['loot_lifecycle'])}; залишилось: {sum(x['remaining'] for x in data['loot_lifecycle'])}")
 print("[3/4] Звіти збережено (4 файли)");print(f"[REPORT] {jp.relative_to(ROOT)}");print(f"[REPORT] {cp.relative_to(ROOT)}");print(f"[REPORT] {ep.relative_to(ROOT)}");print(f"[REPORT] {xp.relative_to(ROOT)}");print("[4/4] PASS" if data["target_reached"] else "[4/4] FAIL");return 0 if data["target_reached"] else 2
if __name__=="__main__":raise SystemExit(main())
