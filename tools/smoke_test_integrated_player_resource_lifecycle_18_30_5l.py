from __future__ import annotations
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from tools.validate_integrated_player_resource_lifecycle import run_fixture
x=run_fixture();assert x['status']=='PASS';assert x['final']['equipment']['durability']==100;assert x['final']['equipment']['refine_level']==2;assert x['final']['equipment']['runes'][0]['stat']=='DEX';assert x['final']['resources']=={'potions':1,'stones':1,'runes':0}
print('[PASS] integrated player/resource lifecycle deterministic fixture')
