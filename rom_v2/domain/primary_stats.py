"""V1-faithful primary-stat state and allocation rules."""
from __future__ import annotations
from dataclasses import dataclass,replace
PRIMARY_KEYS=("str","dex","int","wis","sta")
POINTS_PER_LEVEL=5
BASE_STAT=10
ALIASES={"str":"str","strength":"str","dex":"dex","dexterity":"dex","int":"int","intelligence":"int","wis":"wis","wisdom":"wis","sta":"sta","stamina":"sta"}
def normalize_primary_key(value:object)->str:
 key=str(value or "").strip().lower();result=ALIASES.get(key)
 if result is None:raise ValueError("primary_stat_key_invalid")
 return result
def base_primary_value(level:int)->int:
 if level<1:raise ValueError("character_level_invalid")
 return BASE_STAT+level-1
def earned_points_for_level(level:int)->int:return max(0,level-1)*POINTS_PER_LEVEL
@dataclass(frozen=True,slots=True)
class PrimaryStats:
 str:int=0;dex:int=0;int:int=0;wis:int=0;sta:int=0
 def __post_init__(self)->None:
  if any(value<0 for value in self.values()):raise ValueError("primary_stat_negative")
 def values(self)->tuple[int,...]:return (self.str,self.dex,self.int,self.wis,self.sta)
 def total(self)->int:return sum(self.values())
 def add(self,allocation:dict[str,int])->PrimaryStats:
  values={key:getattr(self,key) for key in PRIMARY_KEYS}
  for raw,amount in allocation.items():
   key=normalize_primary_key(raw)
   if type(amount) is not int or amount<0:raise ValueError("allocation_quantity_invalid")
   values[key]+=amount
  return PrimaryStats(**values)
@dataclass(frozen=True,slots=True)
class AttributePointState:
 allocated:PrimaryStats;free_points:int;total_earned:int
 def __post_init__(self)->None:
  if self.free_points<0 or self.total_earned<0:raise ValueError("attribute_points_negative")
  if self.total_earned!=self.free_points+self.allocated.total():raise ValueError("attribute_point_invariant")
 def allocate(self,allocation:dict[str,int],expected_free_points:int|None=None)->AttributePointState:
  if not allocation:raise ValueError("allocation_empty")
  if expected_free_points is not None and expected_free_points!=self.free_points:raise ValueError("attribute_state_stale")
  normalized:dict[str,int]={}
  for raw,amount in allocation.items():
   key=normalize_primary_key(raw)
   if type(amount) is not int or amount<0:raise ValueError("allocation_quantity_invalid")
   normalized[key]=normalized.get(key,0)+amount
  spent=sum(normalized.values())
  if spent<=0:raise ValueError("allocation_empty")
  if spent>self.free_points:raise ValueError("insufficient_attribute_points")
  return AttributePointState(self.allocated.add(normalized),self.free_points-spent,self.total_earned)
 def respec(self)->AttributePointState:return AttributePointState(PrimaryStats(),self.total_earned,self.total_earned)
 def effective_without_equipment(self,level:int)->PrimaryStats:
  base=base_primary_value(level);return PrimaryStats(*(base+value for value in self.allocated.values()))
