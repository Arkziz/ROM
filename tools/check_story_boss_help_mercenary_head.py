#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static DB-free regression for Mercenary Head story-boss help."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers/story_quest_npc_runtime.py").read_text(encoding="utf-8")
tree=ast.parse(source)
assert source.count('from systems.story_boss_invocation_adapter import HELP_CALLBACK')==1
markup_functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_markup"]
assert len(markup_functions)==2
# The first `_markup(p, ...)` is the base builder. The later TURN_IN wrapper
# delegates to it through `_story_markup_before_turn_in_policy`.
func=[n for n in markup_functions if n.args.args and n.args.args[0].arg=="p"]
assert len(func)==1
text=ast.get_source_segment(source,func[0])
assert "_story_markup_before_turn_in_policy=_markup" in source
assert "definition.number==49" in text
assert "p['npc_id']=='mercenary_head'" in text
assert "'🧭 Як знайти Ватажка'" in text
assert "callback_data=HELP_CALLBACK" in text
assert text.count("callback_data=HELP_CALLBACK")==1
# The button is nested under ACTIVE state and cannot leak into AVAILABLE cards.
active_guard="if q and p['state']=='ACTIVE'"
assert active_guard in text
assert text.index(active_guard)<text.index("definition.number==49")
# Handler and help text remain owned by the existing story-boss wiring.
wiring=(ROOT/"handlers/story_boss_invocation_wiring.py").read_text(encoding="utf-8")
assert "action is StoryBossAction.HELP" in wiring
assert "story_boss_help_text()" in wiring
print("STORY BOSS HELP AT MERCENARY HEAD: PASS")
