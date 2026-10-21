"""Canonical V1-parity equipment enhancement policy."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from random import Random
REFINE_STONE_ITEM_ID=601
SUCCESS_RUNE_ITEM_ID=602
WEAPON_MAX_REFINE_LEVEL=10
ARMOR_MAX_REFINE_LEVEL=6
WEAPON_REFINE_SUCCESS_CHANCES={0:100,1:100,2:100,3:80,4:70,5:60,6:50,7:40,8:30,9:20}
ARMOR_REFINE_SUCCESS_CHANCES={0:100,1:100,2:70,3:50,4:30,5:20}
WEAPON_REFINE_DAMAGE_MULTIPLIERS={0:1.0,1:1.05,2:1.10,3:1.15,4:1.22,5:1.30,6:1.40,7:1.52,8:1.66,9:1.82,10:2.0}
ARMOR_REFINE_BASE_HP_BONUS_PERCENT={0:0.0,1:0.5,2:1.0,3:1.5,4:2.0,5:3.0,6:4.0}
ARMOR_REFINE_RARITY_HP_MULTIPLIERS={"common":1.0,"uncommon":1.1,"rare":1.2,"epic":1.3}
ARMOR_SLOT_KEYS=frozenset({"boots","chest","gloves","helmet","legs","shoulders"})
class EnhancementError(ValueError):pass
class EnhancementFailure(str,Enum):
 NOT_FOUND="NOT_FOUND";NOT_OWNED="NOT_OWNED";NOT_ENHANCEABLE="NOT_ENHANCEABLE";MAX_LEVEL="MAX_LEVEL";RESERVED="RESERVED";INSUFFICIENT_RESOURCES="INSUFFICIENT_RESOURCES";DUPLICATE_OPERATION="DUPLICATE_OPERATION";PERSISTENCE_FAILURE="PERSISTENCE_FAILURE"
def normalize_refine_level(level:int)->int:
 try:return max(0,int(level))
 except Exception:return 0
def get_refine_max_level(kind:str)->int:return WEAPON_MAX_REFINE_LEVEL if kind=="weapon" else ARMOR_MAX_REFINE_LEVEL if kind=="armor" else 0
def get_refine_success_chance(kind:str,current_level:int,use_success_rune:bool=False)->int:
 if use_success_rune:return 100
 table=WEAPON_REFINE_SUCCESS_CHANCES if kind=="weapon" else ARMOR_REFINE_SUCCESS_CHANCES if kind=="armor" else {}
 return int(table.get(normalize_refine_level(current_level),0))
def roll_refine_success(chance:int,rng:Random)->bool:
 """V1 roll is inclusive 1..100 and succeeds when roll <= chance."""
 return rng.randint(1,100)<=max(0,min(100,int(chance)))
def get_refine_failure_level(kind:str,current_level:int)->int:
 """Preserve V1 failure semantics captured by the semantic contract."""
 level=normalize_refine_level(current_level)
 if kind=="weapon" and level>=7:return max(0,level-1)
 if kind=="armor" and level>=4:return max(0,level-1)
 return level
def get_weapon_refine_damage_multiplier(level:int)->float:return WEAPON_REFINE_DAMAGE_MULTIPLIERS.get(normalize_refine_level(level),1.0)
def apply_weapon_refine_to_damage(base_damage:int,level:int)->int:return max(0,int(round(int(base_damage)*get_weapon_refine_damage_multiplier(level))))
def get_armor_refine_hp_bonus_percent(level:int,rarity:str)->float:
 key=str(rarity).lower()
 if key not in ARMOR_REFINE_RARITY_HP_MULTIPLIERS:raise EnhancementError(f"unsupported_rarity:{key}")
 return ARMOR_REFINE_BASE_HP_BONUS_PERCENT.get(normalize_refine_level(level),0.0)*ARMOR_REFINE_RARITY_HP_MULTIPLIERS[key]
@dataclass(frozen=True,slots=True)
class EnhancementItem:
 user_id:int;inventory_id:int;kind:str;refine_level:int;rarity:str="common";durability:int=100;reserved:bool=False
 def __post_init__(self):
  if self.user_id<=0 or self.inventory_id<=0:raise EnhancementError("invalid_identity")
  if self.kind not in {"weapon","armor"}:raise EnhancementError("invalid_kind")
  object.__setattr__(self,"refine_level",normalize_refine_level(self.refine_level))
@dataclass(frozen=True,slots=True)
class EnhancementCommand:
 user_id:int;inventory_id:int;operation_id:str;use_success_rune:bool=False
@dataclass(frozen=True,slots=True)
class EnhancementQuote:
 item:EnhancementItem;chance:int;stone_item_id:int=REFINE_STONE_ITEM_ID;stone_quantity:int=1;success_rune_item_id:int|None=None
@dataclass(frozen=True,slots=True)
class EnhancementResult:
 success:bool;roll_succeeded:bool=False;level_before:int=0;level_after:int=0;failure:EnhancementFailure|None=None;replayed:bool=False
