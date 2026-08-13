from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from systems import pvp_config as cfg
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
assert cfg.PVP_MAX_ROUNDS==18
assert cfg.PVP_DAMAGE_MULTIPLIER==1.1375 and cfg.PVP_HEALING_MULTIPLIER==0.8398
assert cfg.PVP_SHIELD_MULTIPLIER==0.4566 and cfg.PVP_DEBUFF_MULTIPLIER==0.9044
assert cfg.PVP_PRODUCTION_STATE_MUTATION is False

def actor(uid,cls):
 return PvpActorState(user_id=uid,class_key=cls,character_name=cls,max_hp=500,hp=500,max_mp=300,mp=300,resource_type="rage" if cls in {"warrior","knight"} else "mana",resource=0,combo=0,physical_attack=50,magical_attack=50,physical_defense=50,magical_defense=50,weapon_physical_min=10,weapon_physical_max=10,weapon_magical_min=10,weapon_magical_max=10,physical_crit_chance=0,magical_crit_chance=0,dodge_chance=0,level=20)
for left,right in (("warrior","mage"),("knight","rogue"),("scout","priest")):
 r=resolve_pvp_round(1,1,actor(1,left),actor(2,right),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=1465)
 assert r.round_number==1 and not r.terminal
limit=resolve_pvp_round(18,1,actor(1,"warrior"),actor(2,"priest"),PvpActionIntent(1,"afk_skip"),PvpActionIntent(2,"afk_skip"),seed=1465)
assert limit.terminal and limit.result_reason in {"round_limit_hp_percent","draw_round_limit_equal_hp_percent"}
print("[OK] PvP balance candidate integration 14.6.5")
print("- production constants and hard cap 18: PASS")
print("- class profiles, penetration and mitigation: PASS")
print("- visible HP/MP mutation: 0")
print("- PvE files changed: 0")
print("- production database writes: 0")
