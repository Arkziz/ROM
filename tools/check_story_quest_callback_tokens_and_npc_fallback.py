#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-shaped checks for short callbacks and NPC fallback dispatch."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import CALLBACK_PREFIX,_callback_data,_quest_by_number,_markup

def button_data(markup):
 rows=getattr(markup,'keyboard',[]) or []
 return [b.get('callback_data') if isinstance(b,dict) else getattr(b,'callback_data',None) for row in rows for b in row]
def main():
 assert CALLBACK_PREFIX=='sq:'
 seen=set()
 for quest in STORY_QUEST_REGISTRY.values():
  assert _quest_by_number(quest.number).quest_id==quest.quest_id
  for action,npc in (('accept',quest.giver_npc_id),('complete',quest.turn_in_npc_id or quest.giver_npc_id)):
   data=_callback_data(action,npc,quest);assert len(data.encode('utf-8'))<=64;assert data not in seen;seen.add(data)
  p={'npc_id':quest.giver_npc_id,'state':'AVAILABLE','quest':{'quest_id':quest.quest_id,'quest_type':quest.quest_type.value}}
  generated=button_data(_markup(p));assert generated and all(len(x.encode('utf-8'))<=64 for x in generated)
 q4=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==4);assert _callback_data('accept','mercenary_head',q4)=='sq:a:mercenary_head:4'
 source=(ROOT/'handlers/city.py').read_text(encoding='utf-8-sig')
 assert "send_story_npc_if_present(bot, message, 'blacksmith')" in source and 'build_blacksmith_text(user_id)' in source
 assert "send_story_npc_if_present(bot, message, 'mercenary_head')" in source and 'mercenary_head_kb(message.from_user.id)' in source
 assert "send_story_npc_if_present(bot, message, 'alchemist')" not in source
 assert "send_story_npc_if_present(bot, message, 'rune_master')" not in source
 assert 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY and len(STORY_QUEST_REGISTRY)==10
 print('STORY QUEST CALLBACK TOKENS AND NPC FALLBACK: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
