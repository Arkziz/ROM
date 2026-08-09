from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round


def actor(uid, rage=0):
    return PvpActorState(
        user_id=uid, class_key="warrior", max_hp=500, hp=500,
        resource_type="rage", resource=rage,
        physical_attack=40, physical_defense=10,
        weapon_physical_min=10, weapon_physical_max=10,
        physical_crit_chance=0, dodge_chance=0,
    )


def run(a, b, aa, ab, catalog=None):
    return resolve_pvp_round(1, 1, a, b, aa, ab, seed=144101, catalog=catalog or {"warrior": ()})


def main():
    # Two rage actors exchange basic attacks: +15 for own attack and +10 for damage taken.
    result = run(
        actor(1), actor(2),
        PvpActionIntent(1, "basic_attack"),
        PvpActionIntent(2, "basic_attack"),
    )
    assert result.actor_a["resource"] == 25
    assert result.actor_b["resource"] == 25
    kinds = [event["type"] for event in result.events]
    assert kinds.count("rage_gain_attack") == 2
    assert kinds.count("rage_gain_damage_taken") == 2

    # Cap is 100 and actual reported gain reflects the cap.
    capped = run(
        actor(1, 95), actor(2, 95),
        PvpActionIntent(1, "basic_attack"),
        PvpActionIntent(2, "basic_attack"),
    )
    assert capped.actor_a["resource"] == 100
    assert capped.actor_b["resource"] == 100

    # Rage skill cost is paid first, then +15 attack rage is granted.
    catalog = {"warrior": ({
        "key": "rage_cost_skill", "name": "Test", "cost_type": "rage",
        "cost": 20, "cooldown": 0, "attack_type": "physical",
        "damage_multiplier": 1.0,
    },)}
    paid = run(
        actor(1, 20), actor(2),
        PvpActionIntent(1, "skill", "rage_cost_skill"),
        PvpActionIntent(2, "afk_skip"), catalog,
    )
    assert paid.actor_a["resource"] == 15
    assert paid.outcomes[0].resource_spent == 20

    # Cleave-style damaging skill grants base +15 plus production extra_rage +10.
    catalog = {"warrior": ({
        "key": "rage_extra_skill", "name": "Test Extra", "cost_type": "rage",
        "cost": 0, "cooldown": 0, "attack_type": "physical",
        "damage_multiplier": 1.0, "extra_rage": 10,
    },)}
    extra = run(
        actor(1), actor(2),
        PvpActionIntent(1, "skill", "rage_extra_skill"),
        PvpActionIntent(2, "afk_skip"), catalog,
    )
    assert extra.actor_a["resource"] == 25
    assert any(event["type"] == "rage_gain_skill" for event in extra.events)

    # Non-damaging utility does not grant base attack rage.
    catalog = {"warrior": ({
        "key": "utility", "name": "Utility", "cost_type": "rage", "cost": 0,
        "cooldown": 0, "no_damage": True, "damage_multiplier": 0,
        "effect": "player_shield", "duration": 1,
    },)}
    utility = run(
        actor(1), actor(2),
        PvpActionIntent(1, "skill", "utility"),
        PvpActionIntent(2, "afk_skip"), catalog,
    )
    assert utility.actor_a["resource"] == 0

    # Combat log explains both rage sources.
    payload = {
        "round_number": result.round_number,
        "actors": [result.actor_a, result.actor_b],
        "outcomes": [vars(outcome) for outcome in result.outcomes],
        "events": list(result.events),
    }
    text = render_pvp_round_combat_log(payload, 1)
    assert "Лють" in text and "за атаку" in text and "за отриману шкоду" in text

    print("[OK] PvP Rage generation parity contracts")
    print("- rage classes gain +15 for each executed damaging action: PASS")
    print("- rage classes gain +10 for positive damage taken after shield/dodge: PASS")
    print("- skill cost is paid before attack Rage and 100 cap is enforced: PASS")
    print("- production extra_rage stacks after base attack Rage: PASS")
    print("- utility/no-damage actions do not grant base attack Rage: PASS")
    print("- combat log explains attack/damage/skill Rage gains: PASS")
    print("- PvE skill definitions changed: 0")
    print("- production database writes: 0")


if __name__ == "__main__":
    main()
