#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DB-isolated regression for story-boss player context and presentation states."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
source_path = ROOT / "handlers/story_boss_invocation_wiring.py"
source = source_path.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(source_path))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"_player_stats", "_location_id"}]
assert {node.name for node in functions} == {"_player_stats", "_location_id"}
namespace = {"db": SimpleNamespace()}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source_path), "exec"), namespace)
_player_stats = namespace["_player_stats"]
_location_id = namespace["_location_id"]
stats_tuple = (10, 11, 12, 13, 14, 5)
namespace["db"].get_player_stats = lambda user_id: stats_tuple
namespace["db"].get_current_location = lambda user_id: "start_path"
assert _player_stats(1001) == stats_tuple
assert _location_id(1001, stats_tuple) == "start_path"
namespace["db"].get_player_stats = lambda user_id: None
assert _player_stats(1002) is None
namespace["db"].get_current_location = lambda user_id: ""
assert _location_id(1003, {"current_location": "start_path"}) == "start_path"
assert _location_id(1004, SimpleNamespace(location_id="start_path")) == "start_path"
assert "location_id = _location_id(user_id, stats)" in source
assert "dict(getter(user_id) or {})" not in source
from systems.story_boss_invocation_adapter import StoryBossInvocationState, build_story_boss_look_around_presentation
def state(status, current=0):
    return StoryBossInvocationState(quest_number=49, quest_status=status, progress_current=current, progress_target=1, expected_location_id="start_path", current_location_id="start_path", has_active_encounter=False, has_active_travel=False, is_busy=False)
assert build_story_boss_look_around_presentation(state("AVAILABLE")) is None
active = build_story_boss_look_around_presentation(state("ACTIVE"))
assert active is not None and active.text_suffix and active.rows
victory_pending_report = build_story_boss_look_around_presentation(state("ACTIVE", current=1))
assert victory_pending_report is not None and victory_pending_report.text_suffix and victory_pending_report.rows
assert build_story_boss_look_around_presentation(state("COMPLETED", current=1)) is None
print("STORY BOSS PLAYER CONTEXT ADAPTER: PASS")
