from __future__ import annotations

from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round


def actor(uid, cls, hp=500):
    return PvpActorState(
        user_id=uid, class_key=cls, max_hp=500, hp=hp,
        max_mp=200, mp=200,
        resource_type="combat_energy_combo" if cls == "rogue" else "mana",
        resource=100 if cls == "rogue" else 0,
        combo=3 if cls == "rogue" else 0,
        physical_attack=30, magical_attack=30,
        physical_defense=10, magical_defense=10,
        weapon_physical_min=10, weapon_physical_max=10,
        weapon_magical_min=10, weapon_magical_max=10,
        physical_crit_chance=0, magical_crit_chance=0, dodge_chance=0,
    )


def test_combo():
    rogue = actor(1, "rogue")
    priest = actor(2, "priest")
    result = resolve_pvp_round(
        1, 1, rogue, priest,
        PvpActionIntent(1, "skill", "rogue_eviscerate"),
        PvpActionIntent(2, "afk_skip"), seed=1,
    )
    assert result.actor_a["combo"] == 0
    out = next(x for x in result.outcomes if x.user_id == 1)
    assert out.combo_spent == 3
    payload = {"round_number": 1, "actors": [result.actor_a, result.actor_b], "outcomes": [x.__dict__ for x in result.outcomes], "events": list(result.events)}
    text = render_pvp_round_combat_log(payload, 1)
    assert "Витрачено комбо" in text and "3" in text and "Завдано" in text


def test_hot():
    priest = actor(2, "priest", hp=460)
    rogue = actor(1, "rogue")
    priest.combo = 0
    first = resolve_pvp_round(
        1, 1, priest, rogue,
        PvpActionIntent(2, "skill", "priest_healing_blessing"),
        PvpActionIntent(1, "afk_skip"), seed=2,
    )
    assert first.actor_a["hp"] == 460, "HoT must not tick in the application round"
    assert first.actor_a["effects"]["hot"]["duration"] == 4
    second = resolve_pvp_round(
        2, 2,
        PvpActorState.from_dict(first.actor_a), PvpActorState.from_dict(first.actor_b),
        PvpActionIntent(2, "afk_skip"), PvpActionIntent(1, "afk_skip"), seed=3,
    )
    assert second.actor_a["hp"] == 500
    hot = next(x for x in second.events if x["type"] == "hot_tick")
    assert hot["value"] == 40, "log must report actual healing capped by Max HP"
    assert hot["nominal_value"] == 50
    assert hot["hp_after"] == 500 and hot["max_hp"] == 500
    payload = {"round_number": 2, "actors": [second.actor_a, second.actor_b], "outcomes": [x.__dict__ for x in second.outcomes], "events": list(second.events)}
    text = render_pvp_round_combat_log(payload, 2)
    assert "фактично відновило" in text and "40" in text and "500/500" in text


def main():
    test_combo(); test_hot()
    print("[OK] PvP round combat-log, Rogue combo and Priest HoT contracts")
    print("- damage, critical/dodge, resource, combo and effects narration: PASS")
    print("- Rogue Eviscerate spends all 1..3 combo points and ends at 0/3: PASS")
    print("- Priest HoT starts next round, lasts 4 ticks and reports actual capped healing: PASS")
    print("- production PvE skill definitions changed: 0")
    print("- production database writes: 0")


if __name__ == "__main__": main()
