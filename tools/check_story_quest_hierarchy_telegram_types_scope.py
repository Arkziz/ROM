#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PATH=ROOT/"handlers/story_quests.py";SOURCE=PATH.read_text(encoding="utf-8");TREE=ast.parse(SOURCE,filename=str(PATH))
imports=[n for n in TREE.body if isinstance(n,ast.ImportFrom) and n.module=="telebot" and any(alias.name=="types" for alias in n.names)]
assert len(imports)==1
rows=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="story_quest_hierarchy_callback"]
assert len(rows)==1
segment=ast.get_source_segment(SOURCE,rows[0]) or ""
assert 'types.InlineKeyboardButton("🔙 Квести розділу"' in segment
assert "detail_snapshot = build_production_story_quest_detail(" in segment
compile(SOURCE,str(PATH),"exec")
import handlers.story_quests as module
assert hasattr(module,"types")
assert hasattr(module.types,"InlineKeyboardButton")
print("STORY QUEST HIERARCHY TELEGRAM TYPES SCOPE: PASS")
