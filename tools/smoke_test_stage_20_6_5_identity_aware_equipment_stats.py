#!/usr/bin/env python3
from __future__ import annotations
import ast,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.equipment_identity_stat_policy import *
def first(profile):return profile[0][0]
def main():
 assert validate_identity_stat_policy()==()
 expected={
  ('main_hand','staff_2h',''):{'int','wis','sta'},('main_hand','dagger_1h',''):{'dex','str','sta'},
  ('main_hand','bow_2h',''):{'str','dex','sta'},('off_hand','talisman',''):{'int','wis'},
  ('helmet','','cloth'):{'int','wis','sta'},('helmet','','leather'):{'dex','str','sta'},
  ('helmet','','chain'):{'str','sta','dex'},('helmet','','plate'):{'sta','str'},
  ('necklace','',''):{'str','dex','int','wis','sta'},('ring','',''):{'str','dex','int','wis','sta'},
 }
 for (slot,subtype,armor),allowed in expected.items():assert {x for x,_w in get_identity_stat_weights(slot,item_subtype=subtype,armor_type=armor)}==allowed
 base={'bonus_str':1,'bonus_dex':2,'bonus_int':3,'bonus_wis':4,'bonus_sta':5,'pdef':7,'mdef':8}
 for slot,subtype,armor in expected:
  out=redistribute_identity_primary_stats(base,slot,item_subtype=subtype,armor_type=armor,chooser=first)
  assert sum(out['bonus_'+s] for s in PRIMARY_STATS)==15 and out['pdef']==7 and out['mdef']==8
 for args in [('main_hand','unknown',''),('helmet','','unknown'),('unknown','','')]:
  try:get_identity_stat_weights(args[0],item_subtype=args[1],armor_type=args[2])
  except ValueError:pass
  else:raise AssertionError('unknown identity must fail closed')
 rng=random.Random(2065);profile=get_identity_stat_weights('necklace');picks=rng.choices([s for s,_w in profile],weights=[w for _s,w in profile],k=50000)
 assert set(picks)==set(PRIMARY_STATS)
 files={x:(ROOT/x).read_text(encoding='utf-8-sig') for x in ('db_modules/generated_equipment.py','db_modules/shop.py')}
 for x,t in files.items():ast.parse(t,filename=x)
 assert files['db_modules/generated_equipment.py'].count('redistribute_identity_primary_stats(')==2
 assert files['db_modules/shop.py'].count('redistribute_identity_primary_stats(')==1
 assert 'redistribute_primary_stat_budget(' not in ast.get_source_segment(files['db_modules/shop.py'],next(n for n in ast.parse(files['db_modules/shop.py']).body if isinstance(n,ast.FunctionDef) and n.name=='create_common_equipment_shop_preview'))
 print('[OK] weapon/off-hand by subtype, armor by type, jewelry universal random, unknown identity fail-closed PASS')
if __name__=='__main__':main()
