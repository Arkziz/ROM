#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from handlers.story_quest_npc_runtime import _markup,_text,_turn_in_item_action_label

def labels(markup):return [button.text for row in markup.keyboard for button in row]
def main():
 q8=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==8);assert q8.quest_type.value=='TURN_IN'
 view={'quest_id':q8.quest_id,'quest_type':q8.quest_type.value}
 available={'npc_name':'Коваль','npc_id':'blacksmith','state':'AVAILABLE','quest':view}
 text=_text(available);buttons=labels(_markup(available))
 assert '📖 Коротко:' in text and q8.description in text
 assert STORY_QUEST_TEXT[q8.quest_id]['acceptance_text'] not in text
 assert '🔍 Показати ліхтар' in buttons and '✅ Прийняти квест' not in buttons
 active={'npc_name':'Коваль','npc_id':'blacksmith','state':'ACTIVE','quest':view}
 text=_text(active)
 assert '🔍 Висновок:' in text and STORY_QUEST_TEXT[q8.quest_id]['acceptance_text'] in text
 assert 'Зламаний ліхтар вартового' in text
 assert _turn_in_item_action_label(q8,active=True)=='✅ Передати ліхтар'
 q9=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==9)
 assert q9.previous_quest_id==q8.quest_id and q9.giver_npc_id=='mercenary_head'
 assert len(STORY_QUEST_REGISTRY)==10 and not any(q.number==11 for q in STORY_QUEST_REGISTRY.values())
 print('STORY QUEST TURN_IN CONVERSATION FLOW: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
