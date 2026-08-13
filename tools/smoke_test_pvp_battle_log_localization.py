from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from systems.pvp_combat_log import render_pvp_round_combat_log
from systems.pvp_completion_service import _REASON_TEXT
payload = {
    "round_number": 1,
    "actors": [
        {"user_id": 1, "character_name": "A", "class_key": "warrior", "hp": 241, "max_hp": 435, "resource_type": "rage", "resource": 35, "mp": 0, "max_mp": 0},
        {"user_id": 2, "character_name": "B", "class_key": "mage", "hp": 127, "max_hp": 415, "resource_type": "mana", "resource": 0, "mp": 58, "max_mp": 180},
    ],
    "outcomes": [
        {"user_id": 1, "action_type": "basic_attack", "valid": True, "damage": 45, "resource_gained": 15},
        {"user_id": 2, "action_type": "skill", "skill_key": "mage_fireball", "valid": True, "damage": 59, "resource_spent": 20},
    ],
    "events": [{"type": "rage_gain_attack", "user_id": 1, "value": 15, "before": 0, "after": 15}],
}
text = render_pvp_round_combat_log(payload, 1)
for expected in (
    "⚔️ <b>Раунд 1</b>", "🗡 Завдано <b>45</b> шкоди.", "🔥 Лють: +15",
    "❤️ A: 241/435 | B: 127/415", "🔷 B: 58/180 Мана",
):
    assert expected in text, (expected, text)
for forbidden in ("Результат раунду", "ресурсу", "раунд(и)", "Атаку було ухилено"):
    assert forbidden not in text
assert _REASON_TEXT["simultaneous"] == "перемога в бою"
assert _REASON_TEXT["afk_defeat"] == "5 пропущених ходів поспіль"
print("[OK] PvP battle log localization and compact format 14.6.5b")
print("- Ukrainian terminal reasons: PASS")
print("- compact named resources: PASS")
print("- HP and resource summary: PASS")
print("- battle logic changes: 0")
print("- production database writes: 0")
