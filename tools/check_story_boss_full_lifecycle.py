from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def function_segment(source: str, name: str) -> str:
    tree = ast.parse(source)
    rows = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(rows) == 1, (name, len(rows))
    return ast.get_source_segment(source, rows[0]) or ""

# Production boundary must remain unchanged during this validation stage.
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values()) == tuple(range(1, 51))
quest_49 = next(q for q in STORY_QUEST_REGISTRY.values() if q.number == 49)
assert quest_49.quest_type.value == "BOSS"
assert quest_49.boss_key == "pack_leader"
assert quest_49.giver_npc_id == "mercenary_head"
assert (quest_49.turn_in_npc_id or quest_49.giver_npc_id) == "mercenary_head"

adapter = importlib.import_module("systems.story_boss_invocation_adapter")
wiring = importlib.import_module("handlers.story_boss_invocation_wiring")
completion = importlib.import_module("systems.story_quest_boss_completion_system")

# Callback namespace is stable and within Telegram's limit.
callbacks = {
    adapter.INVOKE_CALLBACK,
    adapter.HELP_CALLBACK,
    adapter.RETURN_CALLBACK,
}
assert len(callbacks) == 3
assert all(value.startswith("sqboss:v1:") for value in callbacks)
assert all(len(value.encode("utf-8")) <= 64 for value in callbacks)

# Adapter must expose explicit anti-farm and stale-action concepts.
adapter_source = read("systems/story_boss_invocation_adapter.py")
for token in (
    "ALREADY_DEFEATED",
    "ACTIVE_ENCOUNTER",
    "WRONG_LOCATION",
    "ACTIVE_TRAVEL",
    "INVOKE_CALLBACK",
    "HELP_CALLBACK",
    "RETURN_CALLBACK",
):
    assert token in adapter_source, token

# Live wiring must delegate to the canonical registered boss call owner and must
# not create a second boss factory.
wiring_source = read("handlers/story_boss_invocation_wiring.py")
assert "call_active_story_boss" in wiring_source
assert "build_location_boss" not in wiring_source
assert "register_story_boss_invocation_callbacks" in wiring_source
assert "send_story_boss_look_around_if_present" in wiring_source

city_source = read("handlers/city.py")
assert city_source.count("register_story_boss_invocation_callbacks(bot)") == 1
assert city_source.count("send_story_boss_look_around_if_present(bot, message)") == 1

# Victory bridge must be progress-only and idempotent. It must not complete the
# quest or build the story reward inside combat.
completion_source = read("systems/story_quest_boss_completion_system.py")
segment = function_segment(completion_source, "process_rng_boss_story_completion")
assert "set_story_quest_progress" in segment
assert "already_recorded" in segment
assert "complete_active_story_quest" not in segment
assert "build_story_quest_reward_adapter" not in segment

# Existing focused checkers are the authoritative production-shaped evidence.
required_checkers = (
    "tools/check_story_boss_invocation_adapter.py",
    "tools/check_story_boss_invocation_live_wiring.py",
    "tools/check_story_quest_boss_deferred_completion.py",
)
for rel in required_checkers:
    assert (ROOT / rel).is_file(), rel

# Candidate 49 must preserve the agreed deferred report policy while remaining
# outside production.
candidate_path = ROOT / "Квести/ROM_квести_Початок_Шляху_candidate.json"
doc = json.loads(candidate_path.read_text(encoding="utf-8"))
rows = doc.get("quests", doc) if isinstance(doc, dict) else doc
if isinstance(rows, dict):
    rows = list(rows.values())
q49 = None
for row in rows:
    definition = row.get("definition", row)
    if int(definition.get("number", -1)) == 49:
        q49 = row
        break
assert q49 is not None
definition = q49.get("definition", q49)
assert definition.get("quest_type") == "BOSS"
assert definition.get("giver_npc_id") == "mercenary_head"
assert (definition.get("turn_in_npc_id") or definition.get("giver_npc_id")) == "mercenary_head"
policy = q49.get("boss_story_policy") or definition.get("boss_story_policy") or {}
policy_text = json.dumps(policy, ensure_ascii=False).casefold()
assert "look_around" in policy_text
assert "progress" in policy_text
assert any(token in policy_text for token in ("report", "mercenary", "npc"))

print("STORY BOSS FULL LIFECYCLE CONTRACT: PASS")
