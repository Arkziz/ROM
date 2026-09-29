#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main():
 data=json.loads((ROOT/'Квести'/'ROM_квести_Початок_Шляху_candidate.json').read_text(encoding='utf-8-sig'))
 rows=sorted((q for q in data['quests'] if 11<=int(q['number'])<=20),key=lambda q:int(q['number']));by={q['number']:q for q in rows}
 assert [q['number'] for q in rows]==list(range(11,21))
 assert all(q['unlock_level']==2 and q['reward']['exp']==36 and abs(q['reward']['gold']-0.43)<1e-9 for q in rows)
 assert [q['quest_type'] for q in rows]==['TALK','KILL_REGION','QUEST_ITEM','TURN_IN','QUEST_ITEM','TURN_IN','KILL_REGION','TALK','QUEST_ITEM','TURN_IN']
 for n,key in {13:'start_path_runic_crystal_fragment',15:'start_path_runic_dust_sample',19:'start_path_guard_note'}.items():
  item=by[n]['quest_item'];assert item['item_key']==key and item['drop_chance']==0.15 and item['consume_on_completion'] is False
  assert by[n]['acceptance_text'] and by[n]['completion_text']
  assert 'Герой знаходить' not in by[n]['description'] and 'Герой збирає' not in by[n]['description']
 assert by[13]['turn_in_npc_id']=='rune_master' and by[19]['turn_in_npc_id']=='rune_master'
 assert by[14]['giver_npc_id']==by[14]['turn_in_npc_id']=='alchemist'
 assert [x['item_key'] for x in by[14]['required_quest_items']]==['start_path_runic_crystal_fragment']
 assert [x['item_key'] for x in by[16]['required_quest_items']]==['start_path_runic_dust_sample']
 assert [x['item_key'] for x in by[20]['required_quest_items']]==['start_path_guard_note']
 assert 'передати обидва зразки' not in by[16]['objective_text'].lower() and 'здати обидва зразки' not in by[16]['objective_text'].lower()
 print('STORY QUEST BATCH 11-20 CONTENT: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
