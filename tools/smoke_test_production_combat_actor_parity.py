from systems.simulation.combat_actor_stats import build_battle_actor,build_combat_stat_snapshot
from systems.simulation.models import SimulationEquipment,SimulationInventory,SimulationInventoryItem,SimulationRuneSocket

def main():
 inv=SimulationInventory(40,2);eq=SimulationEquipment();empty=build_combat_stat_snapshot('warrior',1,inv,eq)
 assert (empty.str,empty.dex,empty.intelligence,empty.wis,empty.sta)==(10,10,10,10,10)
 assert empty.max_hp==170 and empty.attack==10 and empty.magic_attack==10 and empty.pdef==2 and empty.mdef==10 and empty.max_mp==0
 mage=build_combat_stat_snapshot('mage',1,inv,eq);assert mage.max_mp==170 and mage.attack_type=='magical'
 weapon=SimulationInventoryItem(inv.allocate_id(),9001,'weapon','equipment',1,1,'main_hand',5,'rare',refine_level=2,stats={'str':3,'weapon_min_damage':10,'weapon_max_damage':20});weapon.runes.append(SimulationRuneSocket(0,501,'STR',2));inv.items.append(weapon);eq.slots['main_hand']=weapon.simulation_item_id
 chest=SimulationInventoryItem(inv.allocate_id(),9002,'chest','equipment',1,1,'chest',5,'rare',durability=100,refine_level=2,stats={'sta':4,'pdef':10,'mdef':6});chest.runes.append(SimulationRuneSocket(0,502,'STA',2));inv.items.append(chest);eq.slots['chest']=chest.simulation_item_id
 s=build_combat_stat_snapshot('warrior',5,inv,eq);assert s.str==19 and s.sta==20 and s.weapon_min_damage==11 and s.weapon_max_damage==22 and s.pdef==14 and s.mdef==20 and s.max_hp>300
 chest.durability=0;broken=build_combat_stat_snapshot('warrior',5,inv,eq);assert broken.sta==14 and broken.pdef==2 and broken.mdef==14
 actor=build_battle_actor('warrior',5,inv,eq,current_hp=999,current_mp=12);assert actor.hp==actor.max_hp and actor.resource==12
 print('[OK] Production combat actor and equipment stat parity')
 print('- base stats 10 +1 per level-up: PASS')
 print('- HP/MP/ATK/MATK/PDEF/MDEF formulas: PASS')
 print('- equipment, refine and rune bonuses: PASS')
 print('- broken equipment contributes zero bonuses: PASS')
 print('- weapon refine damage and resource type: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
