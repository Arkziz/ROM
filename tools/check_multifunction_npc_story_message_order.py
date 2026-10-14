#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import has_story_npc_if_present,send_story_npc_if_present
def name(c):
 f=c.func
 return f.id if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else None
def main():
 src=(ROOT/'handlers'/'city.py').read_text(encoding='utf-8-sig');tree=ast.parse(src);seen=set()
 for n in ast.walk(tree):
  if not isinstance(n,ast.If) or not isinstance(n.test,ast.Call) or name(n.test)!='has_story_npc_if_present' or len(n.test.args)<2:continue
  arg=n.test.args[1]
  if not isinstance(arg,ast.Constant):continue
  calls=[x for st in n.body for x in ast.walk(st) if isinstance(x,ast.Call)];names=[name(x) for x in calls]
  assert 'send_message' in names and 'send_story_npc_if_present' in names
  assert names.index('send_message')<names.index('send_story_npc_if_present');seen.add(arg.value)
 assert {'blacksmith','mercenary_head'}<=seen
 assert callable(has_story_npc_if_present) and callable(send_story_npc_if_present)
 assert len(STORY_QUEST_REGISTRY)==10 and not any(q.number==11 for q in STORY_QUEST_REGISTRY.values())
 assert "send_story_npc_if_present(bot, message, 'alchemist')" not in src
 assert "send_story_npc_if_present(bot, message, 'rune_master')" not in src
 print('MULTIFUNCTION NPC STORY MESSAGE ORDER: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
