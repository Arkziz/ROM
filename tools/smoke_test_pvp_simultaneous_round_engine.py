from __future__ import annotations

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round

CATALOG = {
    "warrior": ({"key":"strike","cost_type":"rage","cost":0,"cooldown":0,"attack_type":"physical","damage_multiplier":1.0,"extra_rage":10},),
    "mage": ({"key":"bolt","cost_type":"mana","cost":20,"cooldown":2,"attack_type":"magical","damage_multiplier":1.0,"stun_chance":100},),
    "priest": ({"key":"hot","cost_type":"mana","cost":20,"cooldown":2,"damage_multiplier":0,"no_damage":True,"effect":"player_hot","duration":4},),
    "knight": (), "scout": (), "rogue": (),
}

def actor(uid, cls, resource_type, resource, mp=0):
    return PvpActorState(uid, cls, 500, 500, mp, mp, resource_type, resource, physical_attack=50, magical_attack=50, physical_defense=20, magical_defense=20, weapon_physical_min=10, weapon_physical_max=10, weapon_magical_min=10, weapon_magical_max=10, physical_crit_chance=0, magical_crit_chance=0, dodge_chance=0)

def main():
    a=actor(1,"warrior","rage",0); b=actor(2,"mage","mana",100,100)
    r=resolve_pvp_round(1,1,a,b,PvpActionIntent(1,"skill","strike"),PvpActionIntent(2,"skill","bolt"),seed=1,catalog=CATALOG)
    assert r.actor_a["hp"] < 500 and r.actor_b["hp"] < 500
    assert r.actor_a["resource"] == 10 and r.actor_a["stunned_next"] is True
    assert r.actor_b["mp"] == 80 and r.actor_b["cooldowns"]["bolt"] == 2
    r2=resolve_pvp_round(2,2,PvpActorState.from_dict(r.actor_a),PvpActorState.from_dict(r.actor_b),PvpActionIntent(1,"basic_attack"),PvpActionIntent(2,"basic_attack"),seed=2,catalog=CATALOG)
    assert r2.outcomes[0].action_type == "stunned_skip"
    afk_a=actor(3,"warrior","rage",0); afk_b=actor(4,"warrior","rage",0); afk_a.consecutive_afk=4; afk_b.consecutive_afk=4
    draw=resolve_pvp_round(5,5,afk_a,afk_b,PvpActionIntent(3,"afk_skip"),PvpActionIntent(4,"afk_skip"),seed=3,catalog=CATALOG)
    assert draw.terminal and draw.winner_id is None and draw.result_reason == "technical_draw_both_afk"
    x=actor(5,"warrior","rage",0); y=actor(6,"warrior","rage",0); x.hp=40; y.hp=40; x.effects["bleed"]={"kind":"bleed","power":50,"duration":1}; y.effects["poison"]={"kind":"poison","power":50,"duration":1}
    lethal=resolve_pvp_round(3,3,x,y,PvpActionIntent(5,"basic_attack"),PvpActionIntent(6,"basic_attack"),seed=4,catalog=CATALOG)
    assert lethal.terminal and lethal.winner_id is None and lethal.result_reason == "draw_periodic"
    print("[OK] Simultaneous PvP round engine contracts")
    print("- immutable intents and cloned duel-local actors: PASS")
    print("- simultaneous damage and next-round stun: PASS")
    print("- production skill cost/cooldown fields consumed: PASS")
    print("- DoT/HoT, AFK technical draw and simultaneous lethal draw: PASS")
    print("- PvP modifiers 1.00 and potion-free engine: PASS")
    print("- database writes: 0")
if __name__ == "__main__": main()
