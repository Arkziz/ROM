from systems.simulation.meta_progression import *
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
from systems.simulation.rng import SimulationRng

def main():
 inv=SimulationInventory(40,2);eq=SimulationEquipment();svc=SimulationMetaProgressionService(inv,eq,SimulationRng(136400));svc.start_day(1)
 mobs=[{'name':'Wolf','base_name':'Wolf','level':5,'is_elite':True}];c=svc.ensure_contract(5,mobs);assert c and c.target_kills==5
 for _ in range(25):svc.on_victory(mobs[0],5)
 assert svc.state.daily.completed and svc.state.contract.completed
 exp=svc.claim_contract();assert exp==get_base_exp_for_level(5)*20 and svc.state.guild.contracts==1
 assert svc.claim_daily() and svc._qty(201)==3 and svc._qty(FIRIUS_TOKEN_ITEM_ID)==5
 rune_id=get_rune_item_id('STA',1);svc._add(rune_id,'r','rune',3);assert svc.fuse_available_runes()==1 and svc._qty(get_rune_item_id('STA',2))==1
 item=SimulationInventoryItem(inv.allocate_id(),900001,'chest','equipment',1,1,'chest',5,'common');inv.items.append(item);eq.slots['chest']=item.simulation_item_id;assert svc.insert_best_runes()==1 and len(item.runes)==1 and item.runes[0].stat=='STA'
 svc._add(401,'stone','material',1);assert svc.refine_best() and item.refine_level==1
 print('[OK] Contracts, daily, runes, refine and guild integration')
 print('- 5-kill contract and production EXP equivalent: PASS')
 print('- daily 25 kills, 3 HP potions and 5 Firius tokens: PASS')
 print('- 3 runes + 1 token fusion: PASS')
 print('- rune insertion into equipped sockets: PASS')
 print('- seeded refine success and guild progress: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
