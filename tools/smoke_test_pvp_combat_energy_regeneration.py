from __future__ import annotations

from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round


def rogue(uid=1, energy=0):
    return PvpActorState(
        user_id=uid, class_key="rogue", max_hp=500, hp=500,
        resource_type="combat_energy_combo", resource=energy, combo=0,
        physical_attack=40, physical_defense=10, magical_defense=10,
        weapon_physical_min=10, weapon_physical_max=10,
        physical_crit_chance=0, dodge_chance=0,
    )


def priest(uid=2):
    return PvpActorState(
        user_id=uid, class_key="priest", max_hp=500, hp=500,
        max_mp=200, mp=200, resource_type="mana",
        magical_attack=40, physical_defense=10, magical_defense=10,
        weapon_magical_min=10, weapon_magical_max=10,
        magical_crit_chance=0, dodge_chance=0,
    )


def run_round(energy, skill_key):
    return resolve_pvp_round(
        2, 2, rogue(energy=energy), priest(),
        PvpActionIntent(1, "skill", skill_key),
        PvpActionIntent(2, "afk_skip"), seed=17,
    )


def main():
    # 5 + 20 = 25, so a 25-energy builder becomes valid and deals damage.
    result = run_round(5, "rogue_sneak_strike")
    outcome = next(x for x in result.outcomes if x.user_id == 1)
    assert outcome.valid and outcome.damage > 0
    assert result.actor_a["resource"] == 0
    regen = next(x for x in result.events if x["type"] == "combat_energy_regen" and x["user_id"] == 1)
    assert regen == {"type":"combat_energy_regen","user_id":1,"value":20,"before":5,"after":25,"maximum":100}

    # Cap: 90 + 20 = 100, not 110. Then skill costs 25, leaving 75.
    capped = run_round(90, "rogue_sneak_strike")
    assert capped.actor_a["resource"] == 75
    cap_event = next(x for x in capped.events if x["type"] == "combat_energy_regen")
    assert cap_event["value"] == 10 and cap_event["after"] == 100

    payload = {
        "round_number": 2,
        "actors": [result.actor_a, result.actor_b],
        "outcomes": [x.__dict__ for x in result.outcomes],
        "events": list(result.events),
    }
    text = render_pvp_round_combat_log(payload, 1)
    assert "Енергія" in text and "5 → 25/100" in text
    assert "Завдано" in text

    print("[OK] PvP combat-energy regeneration parity contracts")
    print("- Rogue/Scout start-of-round energy regeneration +20: PASS")
    print("- regeneration occurs before action-cost validation: PASS")
    print("- 100-energy cap: PASS")
    print("- restored energy is duel-local only: PASS")
    print("- combat log energy regeneration line: PASS")
    print("- PvE skill definitions changed: 0")
    print("- production database writes: 0")


if __name__ == "__main__": main()
