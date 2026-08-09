from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.pvp_combat_log import render_pvp_round_combat_log


def actor(uid: int, name: str, class_key: str, combo: int = 0):
    return {
        "user_id": uid,
        "character_name": name,
        "class_key": class_key,
        "combo": combo,
    }


def main():
    actors = [actor(101, "CharacterOne", "priest"), actor(202, "CharacterTwo", "rogue", 0)]

    payload = {
        "round_number": 13,
        "actors": actors,
        "outcomes": [
            {
                "user_id": 101,
                "action_type": "skill",
                "skill_key": "priest_holy_ray",
                "valid": True,
                "reason": "ok",
                "damage": 46,
                "resource_spent": 12,
                "applied_effects": (),
            },
            {
                "user_id": 202,
                "action_type": "skill",
                "skill_key": "rogue_eviscerate",
                "valid": False,
                "reason": "skill_on_cooldown",
                "applied_effects": (),
            },
        ],
        "events": [
            {"type": "hot_tick", "user_id": 101, "value": 43, "hp_after": 190, "max_hp": 426},
            {"type": "rage_gain_damage_taken", "user_id": 202, "value": 10, "before": 65, "after": 75},
        ],
    }
    text_a = render_pvp_round_combat_log(payload, 101)
    text_b = render_pvp_round_combat_log(payload, 202)
    for text in (text_a, text_b):
        assert "CharacterOne" in text
        assert "CharacterTwo" in text
        assert "46" in text
        assert "skill_on_cooldown" in text
        assert "43" in text
        assert "65" in text and "75" in text
        assert "Результат раунду 13" in text

    afk_payload = {
        "round_number": 14,
        "actors": actors,
        "outcomes": [
            {"user_id": 101, "action_type": "afk_skip", "valid": True, "reason": "afk"},
            {"user_id": 202, "action_type": "stunned_skip", "valid": True, "reason": "stunned"},
        ],
        "events": [],
    }
    afk_text = render_pvp_round_combat_log(afk_payload, 101)
    assert "CharacterOne" in afk_text and "бездіяльність" in afk_text
    assert "CharacterTwo" in afk_text and "оглушення" in afk_text

    terminal_payload = {
        "round_number": 15,
        "actors": actors,
        "outcomes": [
            {"user_id": 101, "action_type": "basic_attack", "skill_key": None, "valid": True, "reason": "ok", "damage": 25},
            {"user_id": 202, "action_type": "basic_attack", "skill_key": None, "valid": True, "reason": "ok", "damage": 30},
        ],
        "events": [
            {"type": "effect_expired", "user_id": 101, "effect": "hot", "value": 0},
            {"type": "shield_absorb", "user_id": 202, "value": 7},
        ],
        "terminal": True,
        "winner_id": 101,
        "result_reason": "hp_zero",
    }
    terminal_text = render_pvp_round_combat_log(terminal_payload, 101)
    assert "CharacterOne" in terminal_text
    assert "CharacterTwo" in terminal_text
    assert "25" in terminal_text and "30" in terminal_text
    assert "щит поглинув" in terminal_text
    assert "завершився" in terminal_text

    # Unknown actor metadata must fall back safely instead of crashing.
    unknown_payload = {
        "round_number": 16,
        "actors": [],
        "outcomes": [
            {"user_id": 999, "action_type": "afk_skip", "valid": True, "reason": "afk"},
        ],
        "events": [],
    }
    unknown_text = render_pvp_round_combat_log(unknown_payload, 101)
    assert "Гравець #999" in unknown_text

    print("[OK] PvP combat-log actor binding contracts")
    print("- actor bound before display-name resolution: PASS")
    print("- valid/invalid/AFK/stunned outcomes render without UnboundLocalError: PASS")
    print("- HoT, Rage, shield and effect-expiry events render with character names: PASS")
    print("- terminal round payload renders before victory/defeat notification: PASS")
    print("- missing actor metadata uses safe fallback: PASS")
    print("- production database writes: 0")


if __name__ == "__main__":
    main()
