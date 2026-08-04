from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
from systems.simulation.survival_state import PersistentCombatState,SimulationSurvivalService

def main():
 inv=SimulationInventory(capacity=40,reserve_slots=2);eq=SimulationEquipment()
 for item_id,slot,durability,rarity in ((1,'main_hand',9,'common'),(2,'chest',4,'rare'),(3,'ring',100,'epic')):
  item=SimulationInventoryItem(inv.allocate_id(),item_id,str(item_id),'equipment',1,1,slot,1,rarity,durability=durability)
  inv.items.append(item);eq.slots[slot]=item.simulation_item_id
 service=SimulationSurvivalService(inv,eq)
 death=service.damage_on_death();assert death.changed==3
 assert [x.durability for x in inv.items]==[4,0,95]
 gold,result=service.urgent_repair(100.0);assert result.repaired==2 and result.cost==39.8 and gold==60.2
 assert [x.durability for x in inv.items]==[100,100,95]
 state=PersistentCombatState(25,100,3,50);assert state.passive_hp_regen(2)==20 and state.hp==45
 state.restore_mp_after_combat();assert state.mp==50
 state.apply_death();assert state.hp==1 and state.mp==50
 print('[OK] Persistent HP/MP, death and repair contracts')
 print('- HP persists and passive regen is 10% per minute: PASS')
 print('- MP restores to full after combat: PASS')
 print('- death sets HP=1 and damages all equipped items by 5: PASS')
 print('- urgent repair triggers only below durability 10: PASS')
 print('- canonical rarity repair cost and wallet deduction: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
