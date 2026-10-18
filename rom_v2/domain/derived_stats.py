"""Source-faithful V1-derived stat formulas for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

PRIMARY_STAT_KEYS=("str","dex","int","wis","sta")
MANA_CLASSES=frozenset({"mage","priest"})
PHYSICAL_ATTACK_SCALING={
 "warrior":{"str":1.0,"dex":0.2,"int":0.0,"wis":0.0,"sta":0.0},
 "knight":{"str":1.1,"dex":0.1,"int":0.0,"wis":0.0,"sta":0.0},
 "rogue":{"str":0.4,"dex":0.8,"int":0.0,"wis":0.0,"sta":0.0},
 "scout":{"str":0.65,"dex":0.55,"int":0.0,"wis":0.0,"sta":0.0},
 "mage":{"str":0.2,"dex":0.0,"int":0.0,"wis":0.0,"sta":0.0},
 "priest":{"str":0.2,"dex":0.0,"int":0.0,"wis":0.0,"sta":0.0},}
MAGICAL_ATTACK_SCALING={
 "warrior":{"str":0.0,"dex":0.0,"int":0.2,"wis":0.0,"sta":0.0},
 "knight":{"str":0.0,"dex":0.0,"int":0.2,"wis":0.0,"sta":0.0},
 "rogue":{"str":0.0,"dex":0.0,"int":0.2,"wis":0.0,"sta":0.0},
 "scout":{"str":0.0,"dex":0.0,"int":0.2,"wis":0.0,"sta":0.0},
 "mage":{"str":0.0,"dex":0.0,"int":1.05,"wis":0.15,"sta":0.0},
 "priest":{"str":0.0,"dex":0.0,"int":0.9,"wis":0.3,"sta":0.0},}
STARTING_HP_BASE=60; HP_PER_LEVEL=20; HP_PER_STAMINA=5
MAX_MP_SCALING={"base":100.0,"level":20.0,"int":1.0,"wis":4.0}
DEFENSE_STAT_COEFFICIENT=0.35
CRIT_BASE_CHANCE=5.0; CRIT_STAT_BASELINE=10.0; CRIT_PER_STAT=0.35
CRIT_SOFT_CAP_TRANSITION_STAT=50.0; CRIT_SOFT_CAP_TRANSITION_CHANCE=19.0; CRIT_SOFT_CAP_ASYMPTOTE=60.0
CRIT_SOFT_CAP_RANGE=CRIT_SOFT_CAP_ASYMPTOTE-CRIT_SOFT_CAP_TRANSITION_CHANCE; CRIT_SOFT_CAP_K=CRIT_SOFT_CAP_RANGE/CRIT_PER_STAT
DODGE_BASE_CHANCE=5.0; DODGE_PER_DEX_DELTA=0.20; DODGE_MIN_CHANCE=1.0
DODGE_SOFT_CAP_TRANSITION_DELTA=40.0; DODGE_SOFT_CAP_TRANSITION_CHANCE=13.0; DODGE_SOFT_CAP_ASYMPTOTE=50.0
DODGE_SOFT_CAP_RANGE=DODGE_SOFT_CAP_ASYMPTOTE-DODGE_SOFT_CAP_TRANSITION_CHANCE; DODGE_SOFT_CAP_K=DODGE_SOFT_CAP_RANGE/DODGE_PER_DEX_DELTA

def _number(value: object)->float:
 try:return float(value or 0)
 except (TypeError,ValueError):return 0.0

def calculate_max_hp(level: object,total_stamina: object)->int:
 return max(1,STARTING_HP_BASE+max(1,int(_number(level) or 1))*HP_PER_LEVEL+max(0,int(_number(total_stamina)))*HP_PER_STAMINA)

def _attack(class_key: object,matrix:Mapping[str,Mapping[str,float]],stats:Mapping[str,object])->int:
 coeff=matrix.get(str(class_key or '').strip().casefold())
 if coeff is None:return 0
 return max(1,int(sum(_number(stats.get(k))*coeff[k] for k in PRIMARY_STAT_KEYS)))

def calculate_patk(class_key:object,stats:Mapping[str,object])->int:return _attack(class_key,PHYSICAL_ATTACK_SCALING,stats)
def calculate_matk(class_key:object,stats:Mapping[str,object])->int:return _attack(class_key,MAGICAL_ATTACK_SCALING,stats)
def calculate_pdef(equipment_pdef:object,total_sta:object)->int:return int(max(0.0,_number(equipment_pdef))+max(0.0,_number(total_sta))*DEFENSE_STAT_COEFFICIENT)
def calculate_mdef(equipment_mdef:object,total_wis:object)->int:return int(max(0.0,_number(equipment_mdef))+max(0.0,_number(total_wis))*DEFENSE_STAT_COEFFICIENT)
def calculate_max_mp(class_key:object,level:object,total_int:object,total_wis:object)->int:
 if str(class_key or '').strip().casefold() not in MANA_CLASSES:return 0
 return max(0,int(MAX_MP_SCALING['base']+_number(level)*MAX_MP_SCALING['level']+_number(total_int)+_number(total_wis)*4.0))
def _crit(stat:object)->float:
 value=_number(stat)
 if value<=50:return 5.0+max(0.0,value-10.0)*0.35
 excess=value-50.0
 return 19.0+CRIT_SOFT_CAP_RANGE*excess/(excess+CRIT_SOFT_CAP_K)
def calculate_physical_crit(total_dex:object)->float:return _crit(total_dex)
def calculate_magical_crit(total_wis:object)->float:return _crit(total_wis)
def calculate_dodge(defender_dex:object,attacker_dex:object)->float:
 delta=_number(defender_dex)-_number(attacker_dex)
 if delta<=-20:return 1.0
 if delta<=40:return 5.0+delta*0.20
 excess=delta-40.0
 return 13.0+DODGE_SOFT_CAP_RANGE*excess/(excess+DODGE_SOFT_CAP_K)
@dataclass(frozen=True)
class DerivedStats:
 max_hp:int; max_mp:int; patk:int; matk:int; pdef:int; mdef:int; physical_crit:float; magical_crit:float; dodge:float

def derive_stats(class_key:str,level:int,stats:Mapping[str,object],equipment_pdef:object=0,equipment_mdef:object=0,attacker_dex:object=0)->DerivedStats:
 return DerivedStats(calculate_max_hp(level,stats.get('sta')),calculate_max_mp(class_key,level,stats.get('int'),stats.get('wis')),calculate_patk(class_key,stats),calculate_matk(class_key,stats),calculate_pdef(equipment_pdef,stats.get('sta')),calculate_mdef(equipment_mdef,stats.get('wis')),calculate_physical_crit(stats.get('dex')),calculate_magical_crit(stats.get('wis')),calculate_dodge(stats.get('dex'),attacker_dex))
