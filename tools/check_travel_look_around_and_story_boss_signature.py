#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AST-only regression for travel look-around and boss-call signature parity."""
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
wiring=(ROOT/"handlers/story_boss_invocation_wiring.py").read_text(encoding="utf-8")
city=(ROOT/"handlers/city.py").read_text(encoding="utf-8")
assert '"current_location_id": location_id' in wiring
assert 'context_kind == \'travel\'' in city
assert 'reply_markup=get_location_context_kb(user_id)' in city
assert "context_kind != 'location'" in city
assert city.index("context_kind == 'travel'") < city.index('send_story_boss_look_around_if_present(bot, message)',city.index('def look_around'))
# Parse the canonical function signature through AST. Importing the call-system
# module reaches db_modules.story_quests and may initialize production SQLite.
call_system=(ROOT/"systems/story_quest_boss_call_system.py").read_text(encoding="utf-8")
call_tree=ast.parse(call_system,filename="systems/story_quest_boss_call_system.py")
functions=[node for node in call_tree.body if isinstance(node,ast.FunctionDef) and node.name=="get_active_story_boss_call"]
assert len(functions)==1
function=functions[0]
positional=[arg.arg for arg in (*function.args.posonlyargs,*function.args.args)]
kwonly=[arg.arg for arg in function.args.kwonlyargs]
parameters=set(positional+kwonly)
assert {"user_id","current_location_id"}.issubset(parameters)
print("TRAVEL LOOK-AROUND AND STORY BOSS SIGNATURE: PASS")
