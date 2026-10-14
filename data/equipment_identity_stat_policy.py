#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical identity-aware primary-stat policy for generated equipment.

Stats follow the item identity, never the class receiving the item:
- main/off hand: item_subtype;
- armor: armor_type;
- jewelry: universal equal-weight primary-stat pool.
"""
from __future__ import annotations

PRIMARY_STATS=("str","dex","int","wis","sta")
BONUS_KEYS={stat:"bonus_"+stat for stat in PRIMARY_STATS}

WEAPON_STAT_WEIGHTS={
 "sword_1h":(("str",50),("sta",35),("dex",15)),
 "sword_2h":(("str",60),("sta",30),("dex",10)),
 "dagger_1h":(("dex",60),("str",30),("sta",10)),
 "wand_1h":(("int",55),("wis",35),("sta",10)),
 "staff_2h":(("int",55),("wis",35),("sta",10)),
 "bow_2h":(("str",45),("dex",45),("sta",10)),
 "crossbow_2h":(("str",45),("dex",45),("sta",10)),
}
OFF_HAND_STAT_WEIGHTS={
 "warrior_shield":(("str",65),("sta",35)),
 "shield":(("sta",65),("str",35)),
 "dagger":(("dex",65),("str",35)),
 "talisman":(("int",55),("wis",45)),
}
ARMOR_STAT_WEIGHTS={
 "cloth":(("int",40),("wis",40),("sta",20)),
 "leather":(("dex",50),("str",30),("sta",20)),
 "chain":(("str",55),("sta",40),("dex",5)),
 "plate":(("sta",65),("str",35)),
}
JEWELRY_STAT_WEIGHTS=tuple((stat,20) for stat in PRIMARY_STATS)

def get_identity_stat_weights(slot_key,*,item_subtype="",armor_type=""):
 """Resolve a fail-closed weighted profile from the persisted item identity."""
 slot=str(slot_key or "");subtype=str(item_subtype or "");armor=str(armor_type or "")
 if slot=="main_hand":profile=WEAPON_STAT_WEIGHTS.get(subtype)
 elif slot=="off_hand":profile=OFF_HAND_STAT_WEIGHTS.get(subtype)
 elif slot in ("necklace","ring"):profile=JEWELRY_STAT_WEIGHTS
 elif slot in ("helmet","shoulders","chest","gloves","legs","boots"):profile=ARMOR_STAT_WEIGHTS.get(armor)
 else:profile=None
 if not profile:raise ValueError(f"Unsupported equipment identity: slot={slot!r}, subtype={subtype!r}, armor_type={armor!r}")
 return profile

def redistribute_identity_primary_stats(stats,slot_key,*,item_subtype="",armor_type="",chooser):
 """Redistribute existing positive primary-stat chunks without changing budget."""
 if not callable(chooser):raise TypeError("chooser must be callable")
 profile=get_identity_stat_weights(slot_key,item_subtype=item_subtype,armor_type=armor_type)
 result=dict(stats);chunks=[]
 for stat in PRIMARY_STATS:
  value=int(result.get(BONUS_KEYS[stat],0) or 0)
  if value>0:chunks.append(value)
  result[BONUS_KEYS[stat]]=0
 for value in chunks:
  selected=str(chooser(profile)).strip().lower()
  if selected not in dict(profile):raise ValueError(f"Chooser returned invalid stat: {selected!r}")
  key=BONUS_KEYS[selected];result[key]=int(result.get(key,0) or 0)+value
 return result

def validate_identity_stat_policy():
 errors=[]
 expected={"sword_1h","sword_2h","dagger_1h","wand_1h","staff_2h","bow_2h","crossbow_2h"}
 if set(WEAPON_STAT_WEIGHTS)!=expected:errors.append("weapon subtype set mismatch")
 if set(OFF_HAND_STAT_WEIGHTS)!={"warrior_shield","shield","dagger","talisman"}:errors.append("off-hand subtype set mismatch")
 if set(ARMOR_STAT_WEIGHTS)!={"cloth","leather","chain","plate"}:errors.append("armor type set mismatch")
 for label,profiles in (("weapon",WEAPON_STAT_WEIGHTS),("off_hand",OFF_HAND_STAT_WEIGHTS),("armor",ARMOR_STAT_WEIGHTS)):
  for key,profile in profiles.items():
   if sum(weight for _stat,weight in profile)!=100:errors.append(f"{label}.{key}: weights must total 100")
   if any(stat not in PRIMARY_STATS or weight<=0 for stat,weight in profile):errors.append(f"{label}.{key}: invalid profile")
 if set(stat for stat,_weight in JEWELRY_STAT_WEIGHTS)!=set(PRIMARY_STATS) or len({weight for _stat,weight in JEWELRY_STAT_WEIGHTS})!=1:errors.append("jewelry must be universal equal-weight")
 return tuple(errors)

_ERRORS=validate_identity_stat_policy()
if _ERRORS:raise ValueError("; ".join(_ERRORS))
