#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.potion_affordability import *
def main():
 assert HP_IDS==(401,403) and MP_IDS==(402,404)
 assert affordable_small("hp",4.99) is None and affordable_small("hp",5)==401
 assert affordable_small("mp",4)==402
 x=PotionAffordabilityLedger();x.record_free_use(401);x.buy_and_use(401);x.buy_and_use(402);r=x.to_dict(20,3)
 assert r["hp_spend"]==5 and r["mp_spend"]==4 and r["total_potion_spend"]==9
 assert r["potion_to_mob_gold_ratio"]==0.45 and r["potion_to_income_after_repairs_ratio"]==round(9/17,6)
 print('[OK] Simulator potion affordability - correct HP/MP routing, canonical purchases and spend ratios')
if __name__=='__main__':main()
