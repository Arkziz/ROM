from __future__ import annotations
from dataclasses import dataclass,field
from typing import Dict,Optional
from .models import SimulationRuneSocket

from data.player_progression import get_base_exp_for_level
from data.runes import FIRIUS_TOKEN_ITEM_ID,RUNE_FUSION_SOURCE_QUANTITY,RUNE_FUSION_TOKEN_QUANTITY,get_rune_definition,get_rune_item_id,get_rune_slot_limit
from systems.refine_system import get_item_refine_kind,get_refine_failure_level,get_refine_max_level,get_refine_success_chance

CONTRACT_UNLOCK_LEVEL=5
CONTRACT_TARGET_KILLS=5
DAILY_CONTRACT_LIMIT=5
CONTRACT_MOBS_EQUIVALENT=20
DAILY_TARGET_KILLS=25
DAILY_REWARD_ITEM_ID=401
DAILY_REWARD_QUANTITY=3
DAILY_FIRIUS_TOKENS=5
REFINE_STONE_ITEM_ID=601
GUILD_ELITE_KILL_EXP_REWARD=25
GUILD_CONTRACT_EXP_REWARD=50
WEAPON_REFINE_SUCCESS_CHANCES={0:100,1:100,2:100,3:80,4:70,5:60,6:50,7:40,8:30,9:20}
ARMOR_REFINE_SUCCESS_CHANCES={0:100,1:100,2:70,3:50,4:30,5:20}

@dataclass
class ContractState:
 target_name:str="";target_level:int=0;target_kills:int=CONTRACT_TARGET_KILLS;current_kills:int=0;reward_exp:int=0;completed:bool=False;claimed:bool=False

@dataclass
class DailyState:
 progress:int=0;target:int=DAILY_TARGET_KILLS;completed:bool=False;claimed:bool=False

@dataclass
class GuildSimulationState:
 exp:int=0;resource:int=0;kills:int=0;contracts:int=0

@dataclass
class SimulationMetaState:
 day:int=0;contracts_completed_today:int=0;contract:Optional[ContractState]=None;daily:DailyState=field(default_factory=DailyState);guild:GuildSimulationState=field(default_factory=GuildSimulationState);rune_fusions:int=0;runes_inserted:int=0;refine_attempts:int=0;refine_successes:int=0

class SimulationMetaProgressionService:
 def __init__(self,inventory,equipment,rng):self.inventory=inventory;self.equipment=equipment;self.rng=rng;self.state=SimulationMetaState()
 def _qty(self,item_id):return sum(i.quantity for i in self.inventory.items if i.item_id==item_id)
 def _consume(self,item_id,quantity):
  need=quantity
  for item in list(self.inventory.items):
   if item.item_id!=item_id:continue
   take=min(item.quantity,need);item.quantity-=take;need-=take
   if item.quantity<=0:self.inventory.items.remove(item)
   if need<=0:break
  return need==0
 def _add(self,item_id,name,category,quantity,max_stack=999):
  from .inventory_engine import InventoryAward,SimulationInventoryEngine
  return SimulationInventoryEngine(self.inventory).award(InventoryAward(item_id,name,category,quantity,max_stack),True)
 def start_day(self,day):
  if day==self.state.day:return
  self.state.day=day;self.state.contracts_completed_today=0;self.state.contract=None;self.state.daily=DailyState()
 def ensure_contract(self,level,available_mobs):
  if level<CONTRACT_UNLOCK_LEVEL or self.state.contract is not None or self.state.contracts_completed_today>=DAILY_CONTRACT_LIMIT:return None
  candidates=[m for m in available_mobs if abs(int(m.get('level',level))-level)<=1]
  if not candidates:return None
  mob=sorted(candidates,key=lambda m:(abs(int(m.get('level',level))-level),str(m.get('name',''))))[0]
  self.state.contract=ContractState(str(mob.get('base_name') or mob.get('name')),int(mob.get('level',level)),reward_exp=get_base_exp_for_level(level)*CONTRACT_MOBS_EQUIVALENT)
  return self.state.contract
 def on_victory(self,mob,level):
  self.state.daily.progress=min(self.state.daily.target,self.state.daily.progress+1);self.state.daily.completed=self.state.daily.progress>=self.state.daily.target
  self.state.guild.kills+=1
  if bool(mob.get('is_elite') or mob.get('elite')):self.state.guild.exp+=GUILD_ELITE_KILL_EXP_REWARD
  c=self.state.contract
  name=str(mob.get('base_name') or mob.get('name'))
  if c and not c.completed and name==c.target_name and int(mob.get('level',0))==c.target_level:
   c.current_kills=min(c.target_kills,c.current_kills+1);c.completed=c.current_kills>=c.target_kills
 def claim_daily(self):
  d=self.state.daily
  if not d.completed or d.claimed:return False
  a=self._add(DAILY_REWARD_ITEM_ID,'Small HP potion','potion',DAILY_REWARD_QUANTITY,99)
  b=self._add(FIRIUS_TOKEN_ITEM_ID,'Firius Token','material',DAILY_FIRIUS_TOKENS,999)
  if a.lost or b.lost:return False
  d.claimed=True;return True
 def claim_contract(self):
  c=self.state.contract
  if not c or not c.completed or c.claimed:return 0
  c.claimed=True;self.state.contracts_completed_today+=1;self.state.guild.exp+=GUILD_CONTRACT_EXP_REWARD;self.state.guild.contracts+=1;reward=c.reward_exp;self.state.contract=None;return reward
 def fuse_available_runes(self):
  count=0
  for item in list(self.inventory.items):
   definition=get_rune_definition(item.item_id)
   if not definition or int(definition['level'])>=5:continue
   while item in self.inventory.items and item.quantity>=RUNE_FUSION_SOURCE_QUANTITY and self._qty(FIRIUS_TOKEN_ITEM_ID)>=RUNE_FUSION_TOKEN_QUANTITY:
    target=get_rune_item_id(definition['stat'],int(definition['level'])+1)
    self._consume(item.item_id,RUNE_FUSION_SOURCE_QUANTITY);self._consume(FIRIUS_TOKEN_ITEM_ID,RUNE_FUSION_TOKEN_QUANTITY);self._add(target,get_rune_definition(target)['name'],'rune',1,999);count+=1
  self.state.rune_fusions+=count;return count
 def insert_best_runes(self):
  inserted=0
  equipped_ids={x for x in self.equipment.slots.values() if x}
  runes=sorted([i for i in self.inventory.items if get_rune_definition(i.item_id)],key=lambda i:get_rune_definition(i.item_id)['level'],reverse=True)
  for equipment in [i for i in self.inventory.items if i.simulation_item_id in equipped_ids]:
   capacity=max(0,int(get_rune_slot_limit(equipment.slot_key)));current=len(equipment.runes)
   while runes and current<capacity:
    rune=runes[0];definition=get_rune_definition(rune.item_id);equipment.runes.append(SimulationRuneSocket(current,rune.item_id,definition['stat'],int(definition['level'])));self._consume(rune.item_id,1);inserted+=1;current+=1
    if rune.quantity<=0:runes.pop(0)
  self.state.runes_inserted+=inserted;return inserted
 def refine_best(self):
  rarity_rank={"common":0,"uncommon":1,"rare":2,"epic":3}
  attempted=False;any_success=False
  while self._qty(REFINE_STONE_ITEM_ID)>0:
   equipped=[i for i in self.inventory.items if i.simulation_item_id in self.equipment.slots.values() and int(i.durability or 0)>0]
   eligible=[]
   for item in equipped:
    info={"category":item.category,"slot_key":item.slot_key,"type":item.item_subtype,"refine_level":item.refine_level}
    kind=get_item_refine_kind(info);level=int(item.refine_level or 0)
    if not kind or level>=get_refine_max_level(kind):continue
    chance=int(get_refine_success_chance(kind,level))
    if chance<50:continue
    eligible.append((item,kind,level,chance))
   if not eligible:break
   item,kind,level,chance=max(eligible,key=lambda row:(int(row[0].item_level or 0),rarity_rank.get(str(row[0].rarity).lower(),-1),int(row[0].simulation_item_id)))
   if not self._consume(REFINE_STONE_ITEM_ID,1):break
   attempted=True;self.state.refine_attempts+=1
   if self.rng.randint(1,100)<=chance:
    item.refine_level=level+1;self.state.refine_successes+=1;any_success=True
   else:item.refine_level=get_refine_failure_level(kind,level)
  return any_success if attempted else False
