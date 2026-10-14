#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Structural and synthetic regression for Stage 19.28.10 sequencing."""
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source_path=ROOT/"handlers/story_quest_npc_runtime.py";source=source_path.read_text(encoding="utf-8");tree=ast.parse(source)
candidates=[]
for node in ast.walk(tree):
 if not isinstance(node,ast.FunctionDef):continue
 decorators=" ".join(ast.get_source_segment(source,d) or "" for d in node.decorator_list)
 text=ast.get_source_segment(source,node) or ""
 if "callback_query_handler" in decorators and "CALLBACK_PREFIX" in decorators and "accept_story_quest_from_npc(" in text and "complete_active_story_quest(" in text:candidates.append(text)
assert len(candidates)==1
text=candidates[0]
# Generic standalone receipts are eliminated; markers live in the one ACTIVE card.
assert "message='Розмову розпочато.'" not in text
assert "else 'Квест прийнято.'" not in text
assert "marker='✅ Розмову розпочато'" in text
assert "else '✅ Квест прийнято'" in text
assert 'f"{marker}\\n\\n{_text(p)}"' in text
# Completion receipt is always sent, but current NPC refresh is conditional on meaningful quest content.
assert "message=_completion_receipt(" in text
assert "if p.get('quest'):" in text
assert text.index("bot.send_message(call.message.chat.id,message)") < text.index("if p.get('quest'):")
# Error paths and canonical mutation owners remain present.
assert "except StoryQuestCompletionError" in text
assert "except (ValueError,KeyError)" in text
assert text.count("accept_story_quest_from_npc(")==1
assert text.count("complete_active_story_quest(")==1
# Production registry ownership matrix: 27 same-NPC, 22 cross-NPC, one story end.
from data.story_quest_content import STORY_QUEST_REGISTRY
quests=sorted(STORY_QUEST_REGISTRY.values(),key=lambda q:q.number);by={q.number:q for q in quests}
same=[];cross=[];end=[]
for q in quests:
 nxt=by.get(q.number+1);completion=q.turn_in_npc_id or q.giver_npc_id
 if nxt is None:end.append(q.number)
 elif nxt.giver_npc_id==completion:same.append(q.number)
 else:cross.append(q.number)
assert len(same)==27 and len(cross)==22 and end==[50]
assert cross==[1,4,5,7,8,9,10,13,16,19,20,24,26,27,32,35,38,39,41,46,47,49]
print("STORY QUEST MESSAGE SEQUENCING: PASS")
