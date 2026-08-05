from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json, os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

SCHEMA_VERSION = "rom.simulation.economic.v2"
LEDGER_VERSION = "13.8.1"
CACHE_SCHEMA = "pve_balance_v2"

def _map(v): return v if isinstance(v, Mapping) else {}
def _num(v, d=0.0):
    try: return float(v)
    except (TypeError, ValueError): return float(d)
def _round(v): return round(_num(v), 6)
def _plain(v):
    if is_dataclass(v): return asdict(v)
    if isinstance(v, Mapping): return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [_plain(x) for x in v]
    return v

@dataclass(frozen=True)
class EconomicLedgerEntry:
    sequence:int; minute:int; day:int; category:str; source:str; amount:float
    balance_before:float; balance_after:float; event_type:str; event_id:str; classified:bool=True

@dataclass
class EconomicLedger:
    initial_cash:float=0.0
    entries:List[EconomicLedgerEntry]=field(default_factory=list)
    def balance_after(self):
        value=self.initial_cash
        for e in self.entries: value += e.amount if e.category in {"faucet","transfer_in"} else -e.amount
        return _round(value)
    def record(self, minute, day, category, source, amount, event_type, event_id, classified=True):
        amount=max(0.0,_num(amount))
        if not amount: return
        before=self.balance_after(); after=before+amount if category in {"faucet","transfer_in"} else before-amount
        self.entries.append(EconomicLedgerEntry(len(self.entries)+1,int(minute or 0),int(day or 0),category,str(source),_round(amount),before,_round(after),str(event_type),str(event_id),bool(classified)))
    def totals(self):
        result={"faucets":0.0,"sinks":0.0,"transfers_in":0.0,"transfers_out":0.0}; keys={"faucet":"faucets","sink":"sinks","transfer_in":"transfers_in","transfer_out":"transfers_out"}
        for e in self.entries: result[keys[e.category]] += e.amount
        return {k:_round(v) for k,v in result.items()}
    def reconcile(self, final_cash):
        t=self.totals(); expected=_round(self.initial_cash+t["faucets"]-t["sinks"]+t["transfers_in"]-t["transfers_out"]); delta=_round(_num(final_cash)-expected)
        return {"initial_cash":_round(self.initial_cash),"expected_final_cash":expected,"actual_final_cash":_round(final_cash),"delta":delta,"passed":abs(delta)<=0.01,"classified_entries":sum(e.classified for e in self.entries),"unclassified_entries":sum(not e.classified for e in self.entries),**t}
    def to_dict(self): return {"version":LEDGER_VERSION,"initial_cash":_round(self.initial_cash),"entries":[asdict(e) for e in self.entries],"totals":self.totals()}

def build_ledger_from_progression(result):
    p=_plain(result); ledger=EconomicLedger()
    for i,raw in enumerate(p.get("events",[]),1):
        e=_plain(raw); d=_map(e.get("details")); et=str(e.get("event_type","")); minute=int(e.get("minute",0) or 0); day=int(e.get("day",0) or 0); eid=f"{et}:{day}:{minute}:{i}"
        if et=="victory": ledger.record(minute,day,"faucet","combat_reward",next((_num(d[k]) for k in ("gold","gold_reward","reward_gold") if k in d),0),et,eid)
        elif et=="city_visit":
            ledger.record(minute,day,"faucet","npc_sale",next((_num(d[k]) for k in ("sale_gold","gold_received") if k in d),0),et,eid)
            ledger.record(minute,day,"sink","repair",_num(d.get("repair_cost")),et,eid)
        elif et in {"contract_claim","daily_claim"}: ledger.record(minute,day,"faucet",et,next((_num(d[k]) for k in ("gold","gold_reward","reward_gold") if k in d),0),et,eid)
    final=_num(p.get("final_gold")); delta=_round(final-ledger.balance_after())
    if abs(delta)>0.01: ledger.record(0,0,"faucet" if delta>0 else "sink","reconciliation_adjustment",abs(delta),"reconciliation","reconciliation:1",False)
    return ledger

def build_asset_snapshot(inventory,equipment,final_cash):
    slots=dict(getattr(equipment,"slots",{}) or {}); equipped={int(v) for v in slots.values() if v is not None}; rows=[]; buckets={"unequipped_inventory":0.0,"equipped_items":0.0,"consumables":0.0,"resources":0.0}; valued=unvalued=0
    for obj in list(getattr(inventory,"items",[]) or []):
        row=_plain(obj); sid=int(row.get("simulation_item_id",0) or 0); qty=max(0,int(row.get("quantity",0) or 0)); explicit="sell_price" in row and row.get("sell_price") is not None; unit=max(0.0,_num(row.get("sell_price"))) if explicit else None; total=_round((unit or 0)*qty); eq=sid in equipped; cat=str(row.get("category","")).lower()
        if explicit:
            valued+=qty; bucket="equipped_items" if eq else "consumables" if cat in {"potion","consumable"} else "resources" if cat in {"material","rune","resource"} else "unequipped_inventory"; buckets[bucket]+=total
        else: unvalued+=qty; bucket="unvalued"
        row.update({"equipped":eq,"equipped_slot":next((s for s,v in slots.items() if v==sid),None),"unit_sell_value":unit,"total_sell_value":total if explicit else None,"valuation_bucket":bucket}); rows.append(row)
    rows.sort(key=lambda x:(not x["equipped"],x.get("slot_key",""),x.get("simulation_item_id",0))); buckets={k:_round(v) for k,v in buckets.items()}; cash=_round(final_cash); coverage="FULL" if unvalued==0 else "PARTIAL" if valued else "UNAVAILABLE"
    return {"schema_version":SCHEMA_VERSION,"cash_gold":cash,"inventory_capacity":int(getattr(inventory,"capacity",0) or 0),"used_slots":len(rows),"free_slots":max(0,int(getattr(inventory,"capacity",0) or 0)-len(rows)),"equipment_slots":slots,"items":rows,"bucket_values":buckets,"total_net_worth":_round(cash+sum(buckets.values())),"valued_items":valued,"unvalued_items":unvalued,"coverage":coverage}

def enrich_progression_result(result,inventory,equipment,scenario):
    p=_plain(result); final=_num(p.get("final_gold")); ledger=build_ledger_from_progression(p); snap=build_asset_snapshot(inventory,equipment,final); v=snap["bucket_values"]
    return {**p,"economic_schema_version":SCHEMA_VERSION,"economic_ledger_version":LEDGER_VERSION,"scenario":dict(scenario),"economic_ledger":ledger.to_dict(),"economic_reconciliation":ledger.reconcile(final),"final_asset_snapshot":snap,"asset_valuation":{"cash_gold":snap["cash_gold"],"inventory_liquidation_value":v["unequipped_inventory"],"equipped_item_value":v["equipped_items"],"consumable_value":v["consumables"],"resource_value":v["resources"],"total_net_worth":snap["total_net_worth"],"valued_items":snap["valued_items"],"unvalued_items":snap["unvalued_items"],"coverage":snap["coverage"]}}

@dataclass(frozen=True,order=True)
class EconomicScenarioSpec:
    character_class:str; profile:str; seed:int; target_level:int; inventory_capacity:int; max_days:int=365; schema_version:str=SCHEMA_VERSION; ledger_version:str=LEDGER_VERSION

class EconomicResultCache:
    def __init__(self,root): self.directory=Path(root)/"simulation_reports"/"cache"/CACHE_SCHEMA; self.directory.mkdir(parents=True,exist_ok=True)
    def key_for(self,spec): return sha256(json.dumps(asdict(spec),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    def path_for(self,spec): return self.directory/f"{self.key_for(spec)}.json"
    def save(self,spec,payload):
        path=self.path_for(spec); tmp=path.with_suffix(f".{os.getpid()}.tmp"); tmp.write_text(json.dumps(dict(payload),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); tmp.replace(path); return path
    def load(self,spec):
        path=self.path_for(spec); return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
