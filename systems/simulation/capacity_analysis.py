from dataclasses import asdict,dataclass
from .drop_inventory import SimulationDropInventoryEngine
from .models import SimulationInventory
from .rng import SimulationRng
@dataclass
class CapacityScenarioResult:
    capacity:int;kills:int;awarded:int;lost:int;full_bag_events:int;used_slots:int;free_slots:int;utilization_percent:float;forced_city_return:bool;lost_value:float
def run_capacity_scenario(capacity,kills,seed,mob,item_resolver,rules=None,reserve_slots=2):
    inv=SimulationInventory(capacity=capacity,reserve_slots=reserve_slots);e=SimulationDropInventoryEngine(inv,SimulationRng(seed),item_resolver);aw=lo=fu=0;value=0.0
    for _ in range(kills):
        r=e.process_enemy(mob,rules);aw+=r.awarded;lo+=r.lost;fu+=r.full_bag_events;value+=r.lost_value
    return CapacityScenarioResult(capacity,kills,aw,lo,fu,inv.used_slots,inv.free_slots,round(inv.utilization*100,4),inv.should_visit_city,value)
def compare_40_60(kills,seed,mob,item_resolver,rules=None):
    a=run_capacity_scenario(40,kills,seed,mob,item_resolver,rules);b=run_capacity_scenario(60,kills,seed,mob,item_resolver,rules)
    return {'baseline_40':asdict(a),'experiment_60':asdict(b),'delta':{'lost':b.lost-a.lost,'full_bag_events':b.full_bag_events-a.full_bag_events,'free_slots':b.free_slots-a.free_slots,'lost_value':round(b.lost_value-a.lost_value,4)}}
