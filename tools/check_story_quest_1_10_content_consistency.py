#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
EXPECTED={
4:'Голова Найманців просить обшукати стежку за старим мостом і пошукати будь-які сліди зниклого патруля.',
5:'Показати Старості знайдений клапоть і з’ясувати, чи належав він міській варті.',
6:'Голова Найманців просить розчистити територію біля старого мосту, де патруль бачили востаннє.',
7:'Слабкий металевий відблиск біля старого мосту може виявитися новим доказом. Потрібно ретельно обшукати місцевість.',
8:'Показати Ковалю зламаний ліхтар і з’ясувати, де та як його пошкодили.',
9:'Голова Найманців просить розчистити вузьку стежку до печер і перевірити, чи міг зниклий патруль пройти цим шляхом.',
10:'Доповісти Старості про сліди, що ведуть до печер, і передати результати пошуків патруля.',
}
def main():
 candidate=json.loads((ROOT/'Квести'/'ROM_квести_Початок_Шляху_candidate.json').read_text(encoding='utf-8-sig'))
 by_candidate={int(q['number']):q for q in candidate['quests']};by_prod={q.number:q for q in STORY_QUEST_REGISTRY.values()}
 for number,text in EXPECTED.items():assert by_candidate[number]['description']==text and by_prod[number].description==text
 for number in (4,7):
  assert by_candidate[number]['acceptance_text']==STORY_QUEST_TEXT[by_prod[number].quest_id]['acceptance_text']
  assert by_candidate[number]['completion_text']==STORY_QUEST_TEXT[by_prod[number].quest_id]['completion_text']
  assert 'Герой знаходить' not in by_prod[number].description
 assert 'знаходить сліди патруля' not in by_prod[9].description and 'відкриває главу' not in by_prod[10].description
 assert abs(by_prod[4].quest_item.drop_chance-0.15)<1e-12 and abs(by_prod[7].quest_item.drop_chance-0.15)<1e-12
 assert by_prod[4].quest_item.consume_on_completion is False and by_prod[7].quest_item.consume_on_completion is False
 assert all(q.reward.exp==30 and abs(q.reward.gold-0.27)<1e-12 for q in by_prod.values())
 assert len(by_prod)==10 and 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
 print('STORY QUEST 1-10 CONTENT CONSISTENCY: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
