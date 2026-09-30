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
assert 'button.get("text") != "🔙 До журналу"' in segment
assert 'keyboard = _inline_markup(hierarchy_rows)' in segment
assert 'keyboard = _inline_markup(detail_snapshot["keyboard"])' not in segment
assert 'types.InlineKeyboardButton("🔙 Квести розділу"' in segment
# Legacy journal remains available only to old messages/callbacks.
assert 'rows.append([_button("🔙 До журналу"' in SOURCE
compile(SOURCE,str(PATH),"exec")
print("STORY QUEST HIERARCHY DETAIL NAVIGATION: PASS")
