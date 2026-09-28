#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
FIELDS={"title","description","acceptance_text","objective_text","completion_text","drop_message","objective_hint","next_step_hint","chapter_completion_text","display_name"}
BAD=("\\n","\\r","\\t")
def walk(value,path="root"):
 if isinstance(value,dict):
  for key,item in value.items():
   child=f"{path}.{key}"
   if isinstance(item,str) and key in FIELDS:yield child,item
   else:yield from walk(item,child)
 elif isinstance(value,list):
  for index,item in enumerate(value):yield from walk(item,f"{path}[{index}]")
def main():
 candidate=json.loads((ROOT/'Квести'/'ROM_квести_Початок_Шляху_candidate.json').read_text(encoding='utf-8-sig'))
 bad=[]
 for path,text in walk(candidate):
  if any(token in text for token in BAD):bad.append(path)
 assert not bad,bad
 for quest in STORY_QUEST_REGISTRY.values():
  strings=[quest.title,quest.description,quest.objective_text]
  if quest.quest_item is not None:strings.append(quest.quest_item.display_name)
  if quest.navigation is not None:strings.extend([quest.navigation.objective_hint,quest.navigation.next_step_hint])
  assert not any(token in text for text in strings if text for token in BAD),(quest.quest_id,strings)
 for quest_id,texts in STORY_QUEST_TEXT.items():
  assert not any(token in text for text in texts.values() if isinstance(text,str) for token in BAD),(quest_id,texts)
 q10=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==10)
 q10_completion=STORY_QUEST_TEXT[q10.quest_id]["completion_text"]
 assert "\\n" not in q10_completion
 assert "\n\n" in q10_completion
 assert len(STORY_QUEST_REGISTRY)==10 and not any(q.number==11 for q in STORY_QUEST_REGISTRY.values())
 print('STORY QUEST LITERAL ESCAPE SEQUENCES: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
