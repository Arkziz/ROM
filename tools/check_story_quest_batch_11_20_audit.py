#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
CANDIDATE=ROOT/'Квести'/'ROM_квести_Початок_Шляху_candidate.json'
def main():
 data=json.loads(CANDIDATE.read_text(encoding='utf-8-sig'))
 rows=sorted((q for q in data['quests'] if 11<=int(q['number'])<=20),key=lambda q:int(q['number']))
 assert [q['number'] for q in rows]==list(range(11,21))
 assert all(q['unlock_level']==2 and q['location_id']=='start_path' for q in rows)
 expected=['TALK','KILL_REGION','QUEST_ITEM','TURN_IN','QUEST_ITEM','TURN_IN','KILL_REGION','TALK','QUEST_ITEM','TURN_IN']
 assert [q['quest_type'] for q in rows]==expected
 assert all(q['reward']['exp']==36 and abs(q['reward']['gold']-0.43)<1e-9 for q in rows)
 by={q['number']:q for q in rows}
 for n,key in {13:'start_path_runic_crystal_fragment',15:'start_path_runic_dust_sample',19:'start_path_guard_note'}.items():
  item=by[n]['quest_item'];assert item['item_key']==key and item['drop_chance']==0.15
 assert by[14]['quest_type']=='TURN_IN' and by[14]['giver_npc_id']==by[14]['turn_in_npc_id']=='alchemist'
 assert [x['item_key'] for x in by[14]['required_quest_items']]==['start_path_runic_crystal_fragment']
 assert [x['item_key'] for x in by[16]['required_quest_items']]==['start_path_runic_dust_sample']
 assert [x['item_key'] for x in by[20]['required_quest_items']]==['start_path_guard_note']
 print('STORY QUEST BATCH 11-20 AUDIT CONTRACT: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
