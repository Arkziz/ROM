#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DB-free lifecycle regression for old story-boss callback payloads."""
import ast
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
source_path=ROOT/"handlers/story_boss_invocation_wiring.py"
source=source_path.read_text(encoding="utf-8");tree=ast.parse(source)
funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
assert "_active_story_boss_callback_call" in funcs
helper=funcs["_active_story_boss_callback_call"]
namespace={"_player_stats":lambda user_id:None,"_location_id":lambda user_id,stats:"start_path","_active_call":None}
def value(obj,*names,default=None):
 for name in names:
  if isinstance(obj,dict) and name in obj:return obj[name]
  if hasattr(obj,name):return getattr(obj,name)
 return default
namespace["_value"]=value
exec(compile(ast.Module(body=[helper],type_ignores=[]),str(source_path),"exec"),namespace)
gate=namespace["_active_story_boss_callback_call"]
def check(payload,allowed):
 namespace["_active_call"]=lambda user_id,location_id:payload
 result=gate(777)
 assert (result is not None)==allowed,(payload,allowed,result)
check(None,False)
check({"quest_number":49,"quest_status":"AVAILABLE","progress_current":0,"progress_target":1},False)
check({"quest_number":49,"quest_status":"ACTIVE","progress_current":0,"progress_target":1},True)
check({"quest_number":49,"quest_status":"ACTIVE","progress_current":1,"progress_target":1},True)
check({"quest_number":49,"quest_status":"COMPLETED","progress_current":1,"progress_target":1},False)
check({"quest_number":49,"quest_status":"SKIPPED","progress_current":1,"progress_target":1},False)
check({"quest_number":48,"quest_status":"ACTIVE","progress_current":0,"progress_target":1},False)
# Structural ordering: shared lifecycle gate precedes every action branch.
callbacks=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="story_boss_invocation_callback"]
assert len(callbacks)==1
text=ast.get_source_segment(source,callbacks[0])
gate_pos=text.index("active_call = _active_story_boss_callback_call(call.from_user.id)")
stale_pos=text.index('"Ця сюжетна дія більше неактуальна."')
help_pos=text.index("StoryBossAction.HELP")
return_pos=text.index("StoryBossAction.RETURN")
presentation_pos=text.index("_presentation_for_user(call.from_user.id)")
assert gate_pos < stale_pos < help_pos < return_pos < presentation_pos
assert text.count("_active_story_boss_callback_call(call.from_user.id)")==1
assert 'current >= target' in text
assert 'data == INVOKE_CALLBACK' in text
assert 'show_alert=True' in text
# No stale HELP/RETURN branch is reachable before the shared gate.
prefix=text[:gate_pos]
assert "story_boss_help_text()" not in prefix and "Повернися до Міста" not in prefix
print("STALE STORY BOSS CALLBACKS: PASS")
