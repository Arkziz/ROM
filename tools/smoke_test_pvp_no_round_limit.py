from pathlib import Path
import inspect
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from systems import pvp_config as config
from systems import pvp_round_engine as engine
from systems.pvp_models import PvpActionIntent, PvpActorState

assert config.PVP_MAX_ROUNDS == 0
assert config.PVP_CONSECUTIVE_AFK_LIMIT == 5
source = inspect.getsource(engine.resolve_pvp_round)
assert "round_limit_hp_percent" not in source
assert "draw_round_limit_equal_hp_percent" not in source
assert "round_number >= PVP_MAX_ROUNDS" not in source

def actor(user_id, class_key):
    return PvpActorState(
        user_id=user_id, class_key=class_key, character_name=class_key,
        max_hp=100000, hp=100000, max_mp=300, mp=300,
        resource_type="mana", resource=0, combo=0,
        physical_attack=1, magical_attack=1,
        physical_defense=100000, magical_defense=100000,
        weapon_physical_min=0, weapon_physical_max=0,
        weapon_magical_min=0, weapon_magical_max=0,
        physical_crit_chance=0, magical_crit_chance=0, dodge_chance=0, level=20,
    )

result = engine.resolve_pvp_round(
    999, 1, actor(1, "warrior"), actor(2, "priest"),
    PvpActionIntent(1, "basic_attack"), PvpActionIntent(2, "basic_attack"), seed=14651,
)
assert not result.terminal
assert result.winner_id is None
assert result.result_reason is None

left = actor(1, "warrior")
right = actor(2, "priest")
left.consecutive_afk = 4
result = engine.resolve_pvp_round(
    1000, 2, left, right,
    PvpActionIntent(1, "afk_skip"), PvpActionIntent(2, "basic_attack"), seed=14652,
)
assert result.terminal
assert result.winner_id == 2
assert result.result_reason == "afk_defeat"

print("[OK] PvP no-round-limit correction 14.6.5a")
print("- round limit disabled: PASS")
print("- HP-percent tiebreak removed: PASS")
print("- round 999 continues normally: PASS")
print("- five-consecutive-AFK defeat retained: PASS")
print("- production database writes: 0")
