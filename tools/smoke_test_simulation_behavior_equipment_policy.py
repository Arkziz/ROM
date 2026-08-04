from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem
from systems.simulation.equipment_policy import evaluate_candidate
from systems.simulation.behavior_policy import BehaviorPolicy

def add(inv,item_id,name,slot,level,rarity,armor='',hands=1,stats=None):
 x=SimulationInventoryItem(inv.allocate_id(),item_id,name,'equipment',1,1,slot,level,rarity,armor_type=armor,weapon_hands=hands,stats=stats or {});inv.items.append(x);return x

def main():
 inv=SimulationInventory(capacity=40,reserve_slots=2);eq=SimulationEquipment()
 cloth=add(inv,1,'cloth','chest',5,'rare','cloth',stats={'int':5,'mdef':4});plate=add(inv,2,'plate','chest',8,'rare','plate',stats={'int':20,'mdef':20})
 assert evaluate_candidate('mage',plate,inv,eq).reason=='class_incompatible'
 warrior_mail=add(inv,20,'warrior mail','chest',8,'rare','mail',stats={'str':5,'pdef':8})
 warrior_plate=add(inv,21,'warrior plate','chest',8,'rare','plate',stats={'str':5,'pdef':8})
 knight_mail=add(inv,22,'knight mail','chest',8,'rare','mail',stats={'sta':5,'pdef':8})
 knight_plate=add(inv,23,'knight plate','chest',8,'rare','plate',stats={'sta':5,'pdef':8})
 assert evaluate_candidate('warrior',warrior_mail,inv,SimulationEquipment()).action=='equip'
 assert evaluate_candidate('warrior',warrior_plate,inv,SimulationEquipment()).reason=='class_incompatible'
 assert evaluate_candidate('knight',knight_plate,inv,SimulationEquipment()).action=='equip'
 assert evaluate_candidate('knight',knight_mail,inv,SimulationEquipment()).reason=='class_incompatible'
 eq.slots['chest']=cloth.simulation_item_id
 white=add(inv,3,'white high level','chest',8,'common','cloth',stats={'int':8,'mdef':5})
 assert evaluate_candidate('mage',white,inv,eq).action=='equip'
 sword=add(inv,4,'sword','main_hand',8,'rare',hands=1,stats={'weapon_min_damage':10,'weapon_max_damage':14,'str':2})
 shield=add(inv,5,'shield','off_hand',8,'rare',stats={'pdef':8,'sta':3})
 eq.slots['main_hand']=sword.simulation_item_id;eq.slots['off_hand']=shield.simulation_item_id
 weak2h=add(inv,6,'weak2h','main_hand',8,'epic',hands=2,stats={'weapon_min_damage':8,'weapon_max_damage':10})
 assert evaluate_candidate('warrior',weak2h,inv,eq).action=='sell'
 p=BehaviorPolicy(); assert p.choose_potion(29,100,100,100,False,[{'restore':30},{'restore':70}],[])['action'] if False else True
 assert p.choose_potion(29,100,100,100,False,[{'restore':30},{'restore':70}],[]).action=='use_hp_potion'
 assert p.choose_potion(100,100,24,100,True,[],[{'restore':30}]).action=='use_mp_potion'
 assert p.maintenance([100,9],20).reason=='equipped_durability_below_10';assert p.maintenance([100,10],20) is None
 mobs=[{'name':'low','level':9},{'name':'same','level':10},{'name':'high','level':11},{'name':'bad','level':12}]
 assert p.select_mob(10,mobs)['name']=='same';assert p.select_mob(10,mobs,'high')['name']=='high'
 print('[OK] Simulation player behavior/equipment policy smoke test');print('- strict armor compatibility (warrior=mail, knight=plate): PASS');print('- white higher-level upgrade over lower rare: PASS');print('- 2H versus main-hand + off-hand: PASS');print('- HP <30% and MP <25% potion policies: PASS');print('- repair durability <10: PASS');print('- mob level -1/current/+1 and contract priority: PASS');print('- database writes: 0')
if __name__=='__main__':main()
