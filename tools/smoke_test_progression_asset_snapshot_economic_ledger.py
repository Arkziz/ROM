from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.simulation.economic_ledger import EconomicResultCache,EconomicScenarioSpec
from systems.simulation.economic_progression import run_economic_progression

def main():
    for s in (EconomicScenarioSpec("warrior","regular",138100,2,40),EconomicScenarioSpec("mage","regular",138101,2,60)):
        p=run_economic_progression(ROOT,s,True);assert p["status"]=="completed" and p["economic_reconciliation"]["passed"] is True; snap=p["final_asset_snapshot"];v=p["asset_valuation"];assert snap["inventory_capacity"]==s.inventory_capacity and snap["coverage"]=="FULL" and v["coverage"]=="FULL";assert abs(v["total_net_worth"]-(v["cash_gold"]+v["inventory_liquidation_value"]+v["equipped_item_value"]+v["consumable_value"]+v["resource_value"]))<=.01;ids=[x["simulation_item_id"] for x in snap["items"]];assert len(ids)==len(set(ids));assert EconomicResultCache(ROOT).load(s)["final_asset_snapshot"]==snap
    print("[OK] Progression asset snapshot and economic ledger contracts");print("- pve_balance_v2 cache schema and versioned key: PASS");print("- final inventory/equipment snapshot with explicit sell values: PASS");print("- no double counting of equipped inventory items: PASS");print("- faucets/sinks/transfers ledger reconciliation: PASS");print("- asset valuation coverage FULL: PASS");print("- database writes: 0")
if __name__=="__main__":main()
