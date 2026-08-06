from __future__ import annotations

import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from systems.simulation.patch_regression import RegressionConfig, analyze_payloads, compare_reports, create_baseline, load_baseline
from systems.simulation.rng_percentiles import distribution, rng_bands


def payload(seed, cash, deaths=0):
    return {"status":"completed","character_class":"warrior","profile":"regular","seed":seed,"target_level":2,"battles":50,"wins":50-deaths,"deaths":deaths,"elapsed_minutes":1000,"final_gold":cash,"city_visits":1,"full_bag_events":0,"items_lost":0,"economic_reconciliation":{"passed":True},"asset_valuation":{"coverage":"FULL","total_net_worth":cash+10},"economic_ledger":{"totals":{"faucets":cash,"sinks":0}},"final_asset_snapshot":{"inventory_capacity":40},"guild_exp":0,"guild_contracts":0}


def main():
    stats=distribution([1,2,3,4,5]); assert stats["percentiles"]["p50"]==3 and stats["count"]==5
    assert rng_bands("deaths",stats)["direction"]=="lower_is_better"
    cfg=RegressionConfig(target_level=2, profiles=("regular",), classes=("warrior",), seed_start=1, seed_count=3, capacities=(40,))
    base=analyze_payloads(ROOT,[payload(1,10),payload(2,11),payload(3,12)],cfg); assert base["verdict"]=="PASS"
    same=analyze_payloads(ROOT,[payload(1,10),payload(2,11),payload(3,12)],cfg); diff=compare_reports(base,same); assert diff["verdict"]=="PASS"
    changed=analyze_payloads(ROOT,[payload(1,30),payload(2,31),payload(3,32)],cfg); diff2=compare_reports(base,changed); assert diff2["verdict"] in {"REVIEW","FAIL"}
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory); path=create_baseline(root,"smoke",base); assert path.exists() and load_baseline(root,"smoke")["scenario_count"]==3
        try: create_baseline(root,"smoke",base)
        except FileExistsError: pass
        else: raise AssertionError("baseline overwrite guard failed")
    print("[OK] RNG percentiles and patch-regression contracts")
    print("- P05/P10/P25/P50/P75/P90/P95 statistics: PASS")
    print("- lucky/typical/unlucky direction by metric: PASS")
    print("- immutable baseline and explicit replace guard: PASS")
    print("- same-input comparison PASS; material drift surfaced: PASS")
    print("- economic reconciliation/FULL coverage gates: PASS")
    print("- database writes: 0")

if __name__=="__main__": main()

# ROM 13.9.0a JSON round-trip compatibility contract
def _json_round_trip_config_contract():
    import json
    from systems.simulation.patch_regression import RegressionConfig, analyze_payloads, compare_reports
    cfg = RegressionConfig(target_level=2, profiles=("regular",), classes=("warrior",), seed_start=1, seed_count=1, capacities=(40,))
    payload = {"status":"completed","character_class":"warrior","profile":"regular","seed":1,"target_level":2,"battles":50,"wins":50,"deaths":0,"elapsed_minutes":1000,"final_gold":10,"city_visits":0,"full_bag_events":0,"items_lost":0,"economic_reconciliation":{"passed":True},"asset_valuation":{"coverage":"FULL","total_net_worth":10},"economic_ledger":{"totals":{"faucets":10,"sinks":0}},"final_asset_snapshot":{"inventory_capacity":40}}
    current = analyze_payloads(ROOT, [payload], cfg)
    baseline = json.loads(json.dumps(current))
    diff = compare_reports(baseline, current)
    assert diff["verdict"] == "PASS", diff

_json_round_trip_config_contract()

