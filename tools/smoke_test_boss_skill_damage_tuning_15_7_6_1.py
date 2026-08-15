from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from data.bosses import BOSS_DEFINITIONS, BOSS_ENCOUNTERS_ENABLED, BOSS_ENCOUNTER_CHANCE_PERCENT

expected = {
    ("pack_leader", "ferocious_bite"): 1.0,
    ("pack_leader", "fang_rend"): 1.4,
    ("pack_leader", "spectral_roar"): 1.3,
    ("pack_leader", "enraged_rend"): 1.7,
    ("goblin_king", "chieftain_axe"): 1.0,
    ("goblin_king", "skull_splitter"): 1.4,
    ("goblin_king", "tyrant_strike"): 1.8,
}
for (boss_key, skill_key), multiplier in expected.items():
    actual = BOSS_DEFINITIONS[boss_key]["skills"][skill_key]["damage_multiplier"]
    assert actual == multiplier, (boss_key, skill_key, actual, multiplier)

assert BOSS_DEFINITIONS["pack_leader"]["skills"]["fang_rend"]["bleed_turns"] == 2
assert BOSS_DEFINITIONS["pack_leader"]["skills"]["fang_rend"]["bleed_damage_fraction"] == 0.20
assert BOSS_DEFINITIONS["pack_leader"]["enrage"]["permanent_attack_buff_percent"] == 25
assert BOSS_DEFINITIONS["goblin_king"]["skills"]["battle_cry"]["attack_buff_percent"] == 15
assert BOSS_DEFINITIONS["goblin_king"]["skills"]["defense_command"]["pdef_buff_percent"] == 30
assert BOSS_DEFINITIONS["goblin_king"]["enrage"]["permanent_attack_buff_percent"] == 30

print("[PASS] boss skill tuning contract", {
    "fang_rend": 1.4,
    "enraged_rend": 1.7,
    "skull_splitter": 1.4,
    "tyrant_strike": 1.8,
    "boss_gate": BOSS_ENCOUNTERS_ENABLED,
    "boss_chance": BOSS_ENCOUNTER_CHANCE_PERCENT,
})
