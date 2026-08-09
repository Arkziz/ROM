from __future__ import annotations

from pathlib import Path

from systems.pvp_action_validation import (
    projected_round_cooldown,
    projected_round_resource,
    validate_pvp_action_choice,
)


def main():
    root = Path(__file__).resolve().parents[1]
    rogue_catalog = {"rogue": (
        {"key": "rogue_hit", "name": "Удар", "cost_type": "combat_energy", "cost": 25, "cooldown": 2},
        {"key": "rogue_finisher", "name": "Потрошіння", "cost_type": "combat_energy_combo", "cost": 40, "min_combo": 1, "cooldown": 3},
    )}
    priest_catalog = {"priest": ({"key": "priest_ray", "name": "Святий промінь", "cost_type": "mana", "cost": 12, "cooldown": 2},)}
    rogue = {"class_key": "rogue", "resource_type": "combat_energy_combo", "resource_value": 5, "combo": 0, "cooldowns": {"rogue_hit": 3}, "mp": 0}
    assert projected_round_resource(rogue) == 25
    assert projected_round_cooldown(rogue, "rogue_hit") == 2
    blocked = validate_pvp_action_choice(rogue, "skill", "rogue_hit", catalog=rogue_catalog)
    assert not blocked["success"] and blocked["reason"] == "skill_on_cooldown" and blocked["remaining"] == 2
    assert "Оберіть іншу дію" in blocked["message"]
    assert validate_pvp_action_choice(rogue, "basic_attack", catalog=rogue_catalog)["success"]
    no_combo = dict(rogue); no_combo["cooldowns"] = {}; no_combo["resource_value"] = 40
    blocked = validate_pvp_action_choice(no_combo, "skill", "rogue_finisher", catalog=rogue_catalog)
    assert blocked["reason"] == "not_enough_combo"
    with_combo = dict(no_combo); with_combo["combo"] = 3
    assert validate_pvp_action_choice(with_combo, "skill", "rogue_finisher", catalog=rogue_catalog)["success"]
    priest = {"class_key": "priest", "resource_type": "mana", "mp": 5, "cooldowns": {}}
    assert validate_pvp_action_choice(priest, "skill", "priest_ray", catalog=priest_catalog)["reason"] == "not_enough_mana"

    handler = (root / "handlers" / "pvp_round_ui.py").read_text(encoding="utf-8")
    validate_pos = handler.index("validate_pvp_action_choice(own,action,skill)")
    submit_pos = handler.index("result=submit_pvp_action", validate_pos)
    assert validate_pos < submit_pos
    between = handler[validate_pos:submit_pos]
    assert 'if not validation.get("success")' in between
    assert "return" in between

    combat_log = (root / "systems" / "pvp_combat_log.py").read_text(encoding="utf-8")
    assert 'who = _actor_display_name(actor, uid)' in combat_log
    assert 'who = "Ви" if uid == viewer else "Суперник"' not in combat_log
    round_ui = (root / "systems" / "pvp_round_ui.py").read_text(encoding="utf-8")
    assert "_participant_display_name(viewer)" in round_ui
    assert "pvp_skill_button_state" in round_ui

    print("[OK] PvP action prevalidation, retry and character-name UI contracts")
    print("- cooldown/resource/combo checked before action persistence: PASS")
    print("- invalid choice keeps the round open for another action: PASS")
    print("- projected cooldown tick and +20 Combat Energy parity: PASS")
    print("- skill buttons expose cooldown/locked state: PASS")
    print("- combat log and round panel use character names: PASS")
    print("- production database writes: 0")


if __name__ == "__main__":
    main()
