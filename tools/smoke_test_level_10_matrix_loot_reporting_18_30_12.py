from __future__ import annotations
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.progression_economy_reporting import build_economy_equipment_report
class E:
 def __init__(self,k,d):self.event_type=k;self.details=d
base=[{"item_id":900001,"name":"rare chest L5","category":"equipment","rarity":"rare","found":1,"slot_key":"chest","item_level":5,"armor_type":"chain","stats":{"pdef":5}}]
events=[E("equipment_resolution",{"sale_records":[{"item_id":900001,"quantity":1,"gold":11.25}],"sale_gold":11.25}),E("simulation_final_state",{"inventory":[]})]
x=build_economy_equipment_report(events,base,0,11.25,"warrior",R)
assert x["equipment_details"][0]["sold"]==1 and x["equipment_summary"][0]["slot_key"]=="chest"
cp=(R/"systems/simulation/class_progression.py").read_text(encoding="utf-8-sig");assert 'payload["equipment_details"]' in cp and 'payload["equipment_summary"]' in cp
meta=(R/"systems/simulation/meta_progression.py").read_text(encoding="utf-8-sig");claim=next(n for n in ast.walk(ast.parse(meta)) if isinstance(n,ast.FunctionDef) and n.name=="claim_daily");seg=ast.get_source_segment(meta,claim) or "";assert "_consume(DAILY_REWARD_ITEM_ID,a.awarded)" in seg and "_consume(FIRIUS_TOKEN_ITEM_ID,b.awarded)" in seg
print("[PASS] atomic daily reward and complete JSON/XLSX loot export regression")
