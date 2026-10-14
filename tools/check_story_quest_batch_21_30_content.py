#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
P=ROOT/'Квести/ROM_квести_Початок_Шляху_candidate.json'
payload=json.loads(P.read_text(encoding='utf-8-sig'))
rows=payload if isinstance(payload,list) else next(payload[k] for k in ('quests','story_quests','rows','data') if isinstance(payload.get(k),list))
def d(r):return r.get('definition',r)
def n(r):return int(d(r).get('number',r.get('number',-1)))
by={n(r):r for r in rows}
expected={23:'start_path_guards_ring',26:'start_path_damaged_guard_shield',29:'start_path_torn_guard_cloak'}
for q,item_key in expected.items():
    qi=d(by[q]).get('quest_item') or by[q].get('quest_item')
    assert qi['item_key']==item_key and qi['consume_on_completion'] is False
    assert abs(float(qi['drop_chance'])-.15)<1e-12
assert str(d(by[24])['quest_type']).upper()=='TALK'
assert all(x.get('consume') is False for x in d(by[24]).get('required_quest_items',[]))
req=d(by[30]).get('required_quest_items',[])
assert str(d(by[30])['quest_type']).upper()=='TURN_IN'
assert len(req)==3 and {x['item_key'] for x in req}==set(expected.values())
assert all(x.get('consume') is True and int(x.get('quantity',0))==1 for x in req)
from data.story_quest_content import STORY_QUEST_REGISTRY
assert sorted(q.number for q in STORY_QUEST_REGISTRY.values())==list(range(1,21))
print('STORY QUESTS 21-30 CONTENT: PASS')
