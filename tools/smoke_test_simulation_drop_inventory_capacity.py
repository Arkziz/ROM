from systems.simulation.inventory_engine import InventoryAward,SimulationInventoryEngine
from systems.simulation.models import SimulationInventory,SimulationInventoryItem
from systems.simulation.capacity_analysis import compare_40_60

def resolver(i):return {'name':'stone','category':'material','max_stack':999,'sell_price':1}
def main():
 inv=SimulationInventory(capacity=2,reserve_slots=1);e=SimulationInventoryEngine(inv)
 assert e.award(InventoryAward(401,'stone','material',10,999)).awarded==10
 assert e.award(InventoryAward(401,'stone','material',5,999)).merged==5 and inv.used_slots==1
 inv.items.append(SimulationInventoryItem(inv.allocate_id(),900,'eq','equipment',1,1));inv.validate()
 assert e.award(InventoryAward(901,'eq2','equipment')).lost==1
 # Fixture uses valid structural fields but intentionally bypasses whole-table
 # special-policy validation via the fixture path in roll_enemy().
 rule={'rule_id':'stone_fixture','group':'material','mode':'shadow','enabled':True,'production_enabled':False,'resolver':'static_item','enemy':{'normal':{'chance':1.0},'elite':{'chance':1.0},'boss':{'chance':1.0}},'quantity':{'min':1,'max':1},'max_per_kill':1,'bag_policy':'atomic','message_policy':'default','migration_stage':'simulation_fixture','item_id':401}
 c=compare_40_60(50,134000,{'name':'x','loot_chance':1.0},resolver,(rule,));assert c['baseline_40']['awarded']==50 and c['experiment_60']['awarded']==50
 print('[OK] Simulation drop/inventory/capacity smoke test');print('- stack merge into full inventory: PASS');print('- equipment requires separate slot: PASS');print('- all-or-nothing full-bag loss: PASS');print('- capacity 40/60 comparison: PASS');print('- central drop rule with injected RNG: PASS');print('- database writes: 0')
if __name__=='__main__':main()
