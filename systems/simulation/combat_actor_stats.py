from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from data.classes import CLASS_CONFIGS
from systems.refine_system import apply_weapon_refine_to_damage,get_armor_refine_hp_bonus_percent
from .battle_models import BattleActor
from .models import SimulationEquipment,SimulationInventory
from data.player_hp import calculate_base_max_hp
from systems.stat_system import calculate_magical_attack,calculate_max_mp,calculate_physical_attack,calculate_physical_defense,calculate_magical_defense,resolve_basic_attack_type

BASE_STAT=10
ARMOR_SLOTS={"helmet","shoulders","chest","gloves","legs","boots"}

@dataclass(frozen=True)
class CombatStatSnapshot:
 str:int;dex:int;intelligence:int;wis:int;sta:int;level:int;max_hp:int;max_mp:int;attack:int;magic_attack:int;pdef:int;mdef:int;weapon_min_damage:int;weapon_max_damage:int;attack_type:str;resource_type:str

def _equipped(inventory,equipment):
 by_id={x.simulation_item_id:x for x in inventory.items};return [by_id[x] for x in equipment.slots.values() if x in by_id]

def build_combat_stat_snapshot(character_class:str,level:int,inventory:SimulationInventory,equipment:SimulationEquipment)->CombatStatSnapshot:
 level=max(1,int(level));base=BASE_STAT+level-1;stats={"str":base,"dex":base,"int":base,"wis":base,"sta":base};item_pdef=item_mdef=0;armor_refine=0.0;weapon_min=weapon_max=0
 for item in _equipped(inventory,equipment):
  if int(item.durability or 0)<=0:continue
  for key in stats:stats[key]+=int(item.stats.get(key,item.stats.get(f"bonus_{key}",0)) or 0)
  item_pdef+=int(item.stats.get("pdef",0) or 0);item_mdef+=int(item.stats.get("mdef",0) or 0)
  for rune in item.runes:
   key=str(rune.stat).strip().lower();
   if key=="int":key="int"
   if key in stats:stats[key]+=int(rune.level)
  if item.slot_key in ARMOR_SLOTS:armor_refine+=float(get_armor_refine_hp_bonus_percent(item.refine_level,item.rarity) or 0.0)
  if item.slot_key=="main_hand":
   raw_min=int(item.stats.get("weapon_min_damage",item.stats.get("weapon_min_magic_damage",0)) or 0);raw_max=int(item.stats.get("weapon_max_damage",item.stats.get("weapon_max_magic_damage",0)) or 0)
   weapon_min,weapon_max=apply_weapon_refine_to_damage(raw_min,raw_max,item.refine_level)
 base_max_hp=calculate_base_max_hp(level,stats["sta"]);max_hp=max(1,int(round(base_max_hp*(1+armor_refine/100.0))))
 mana=CLASS_CONFIGS[character_class]["resource"]=="mana";max_mp=calculate_max_mp(character_class,level=level,intelligence=stats["int"],wisdom=stats["wis"]) if mana else 0
 attack_type=resolve_basic_attack_type(character_class)
 physical_attack=calculate_physical_attack(character_class,strength=stats["str"],dexterity=stats["dex"],intelligence=stats["int"],wisdom=stats["wis"],stamina=stats["sta"])
 magical_attack=calculate_magical_attack(character_class,strength=stats["str"],dexterity=stats["dex"],intelligence=stats["int"],wisdom=stats["wis"],stamina=stats["sta"])
 pdef=calculate_physical_defense(equipment_pdef=item_pdef,stamina=stats["sta"]);mdef=calculate_magical_defense(equipment_mdef=item_mdef,wisdom=stats["wis"])
 return CombatStatSnapshot(stats["str"],stats["dex"],stats["int"],stats["wis"],stats["sta"],level,max_hp,max_mp,physical_attack,magical_attack,pdef,mdef,weapon_min,weapon_max,attack_type,CLASS_CONFIGS[character_class]["resource"])

def build_battle_actor(character_class,level,inventory,equipment,current_hp=None,current_mp=None):
 s=build_combat_stat_snapshot(character_class,level,inventory,equipment);mana=s.resource_type=="mana";max_resource=s.max_mp if mana else 100;resource=max_resource if current_mp is None else max(0,min(int(current_mp),max_resource));hp=s.max_hp if current_hp is None else max(1,min(int(current_hp),s.max_hp))
 return BattleActor(character_class,s.level,hp,s.max_hp,s.attack,s.magic_attack,s.pdef,s.mdef,s.dex,s.wis,s.sta,s.attack_type,s.weapon_min_damage,s.weapon_max_damage,s.resource_type,resource,max_resource)
