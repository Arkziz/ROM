#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static, DB-free visibility gate contract."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers/story_boss_invocation_wiring.py").read_text(encoding="utf-8")
tree=ast.parse(source)
func=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_presentation_for_user"]
assert len(func)==1
text=ast.get_source_segment(source,func[0])
assert '_value(call, "allowed", default=False) is not True' in text
assert text.index('_active_call(user_id, location_id)') < text.index('_value(call, "allowed", default=False) is not True')
assert text.index('_value(call, "allowed", default=False) is not True') < text.index('StoryBossInvocationState')
# Truth table for the exact fail-closed predicate, without importing game modules.
def visible(call):
    allowed=call.get("allowed",False) if isinstance(call,dict) else False
    return bool(call) and allowed is True
for denied in (None,{}, {"allowed":False,"reason":"no_active_quest"},{"allowed":False,"reason":"objective_type_mismatch"},{"reason":"active_boss_quest"},{"allowed":1}):assert visible(denied) is False
assert visible({"allowed":True,"reason":"active_boss_quest"}) is True
print("STORY BOSS CALL VISIBILITY GATE: PASS")
