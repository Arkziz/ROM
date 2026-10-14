"""Canonical simulator-only potion purchase and affordability instrumentation."""
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Dict,Iterable
POTION_CATALOG={401:{"kind":"hp","restore":50,"buy_price":5.0},403:{"kind":"hp","restore":120,"buy_price":15.0},402:{"kind":"mp","restore":40,"buy_price":4.0},404:{"kind":"mp","restore":100,"buy_price":12.5}}
HP_IDS=(401,403);MP_IDS=(402,404)
@dataclass
class PotionAffordabilityLedger:
 bought:Dict[int,int]=field(default_factory=dict);used_free:Dict[int,int]=field(default_factory=dict);used_bought:Dict[int,int]=field(default_factory=dict);spend_hp:float=0.0;spend_mp:float=0.0
 def record_free_use(self,item_id:int):self.used_free[item_id]=self.used_free.get(item_id,0)+1
 def buy_and_use(self,item_id:int):
  row=POTION_CATALOG[item_id];self.bought[item_id]=self.bought.get(item_id,0)+1;self.used_bought[item_id]=self.used_bought.get(item_id,0)+1
  if row["kind"]=="hp":self.spend_hp=round(self.spend_hp+row["buy_price"],2)
  else:self.spend_mp=round(self.spend_mp+row["buy_price"],2)
 def to_dict(self,gold_from_mobs:float,repair_spend:float=0.0):
  total=round(self.spend_hp+self.spend_mp,2);income=float(gold_from_mobs);after=max(0.0,income-float(repair_spend))
  ratio=lambda cost,base:None if base<=0 else round(cost/base,6)
  return {"bought":dict(self.bought),"used_free_or_dropped":dict(self.used_free),"used_bought":dict(self.used_bought),"hp_spend":self.spend_hp,"mp_spend":self.spend_mp,"total_potion_spend":total,"repair_spend":round(float(repair_spend),2),"potion_to_mob_gold_ratio":ratio(total,income),"potion_to_income_after_repairs_ratio":ratio(total,after),"mandatory_spend":round(total+float(repair_spend),2)}
def inventory_potions(items:Iterable,ids):return [{"item_id":i.item_id,"restore":POTION_CATALOG[i.item_id]["restore"],"simulation_item_id":i.simulation_item_id} for i in items if i.item_id in ids and i.quantity>0]
def affordable_small(kind:str,gold:float):
 item_id=401 if kind=="hp" else 402;row=POTION_CATALOG[item_id];return item_id if float(gold)+1e-9>=row["buy_price"] else None
