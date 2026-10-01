#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
city=(ROOT/"handlers/city.py").read_text(encoding="utf-8")
wiring=(ROOT/"handlers/story_boss_invocation_wiring.py").read_text(encoding="utf-8")
assert city.count("send_story_boss_look_around_if_present(bot, message)")==1
assert city.count("register_story_boss_invocation_callbacks(bot)")==1
assert city.index("register_story_boss_invocation_callbacks(bot)") < city.index("@bot.message_handler", city.index("def register_city_handlers"))
assert "call_active_story_boss" in wiring and "build_location_boss" not in wiring
assert "sqboss:v1:" in wiring and "story_boss_invocation_callback" in wiring
assert "get_active_story_boss_call" in wiring
ast.parse(city);ast.parse(wiring)
import handlers.story_boss_invocation_wiring
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,41))
print("STORY BOSS LIVE OWNER WIRING: PASS")
