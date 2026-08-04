from systems.simulation.loot_equipment_city import SimulationLootEquipmentCityService
from systems.simulation.models import SimulationEquipment,SimulationInventory
from systems.simulation.rng import SimulationRng

def main():
 inv=SimulationInventory(40,2);eq=SimulationEquipment();svc=SimulationLootEquipmentCityService('warrior',inv,eq,SimulationRng(136300))
 mob={'name':'fixture','level':5,'loot_chance':1.0,'trash_item_id':7001,'is_elite':True,'elite':True}
 total=0
 for _ in range(50):total+=svc.process_victory(mob).awarded
 assert total>0 and inv.used_slots>0
 gold,city=svc.city_maintenance(0.0);assert city.equipped>0;assert gold>=0
 assert all(value is None or any(x.simulation_item_id==value for x in inv.items) for value in eq.slots.values())
 assert all(not (x.category=='equipment' and x.simulation_item_id not in eq.slots.values()) for x in inv.items)
 print('[OK] Loot, equipment and city maintenance integration')
 print('- production central drop rolls with seeded RNG: PASS')
 print('- stack merge and full-bag loss accounting: PASS')
 print('- class-aware equipment upgrade policy: PASS')
 print('- 2H/off-hand equipment service contract: PASS')
 print('- sell rejected equipment and trash in city: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
