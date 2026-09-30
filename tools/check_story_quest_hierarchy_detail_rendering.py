#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PATH=ROOT/"handlers/story_quests.py";SOURCE=PATH.read_text(encoding="utf-8");TREE=ast.parse(SOURCE,filename=str(PATH))
rows=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="story_quest_hierarchy_callback"]
assert len(rows)==1
segment=ast.get_source_segment(SOURCE,rows[0]) or ""
assert "render_story_quest_detail(user_id, quest.quest_id)" not in segment
assert "render_story_quest_detail(user_id, quest)" not in segment
for token in ("build_production_story_quest_detail(","db.conn","user_id=user_id","quest_id=quest.quest_id","player_level=level","render_story_quest_detail(detail_item)",'detail_snapshot["text"]','_inline_markup(detail_snapshot["keyboard"])',"🔙 Квести розділу"):
 assert token in segment,token
compile(SOURCE,str(PATH),"exec")
from handlers.story_quests import render_story_quest_detail,build_production_story_quest_detail
print("STORY QUEST HIERARCHY DETAIL RENDERING: PASS")
