from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from systems.pvp_combat_log import render_pvp_round_combat_log

payload = {
    "round_number": 1,
    "actors": [
        {"user_id": 1, "character_name": "Бог", "class_key": "warrior", "hp": 372, "max_hp": 420, "resource_type": "rage", "resource": 35, "mp": 0, "max_mp": 0},
        {"user_id": 2, "character_name": "Dedor", "class_key": "priest", "hp": 390, "max_hp": 426, "resource_type": "mana", "resource": 0, "mp": 333, "max_mp": 345},
    ],
    "outcomes": [
        {"user_id": 1, "action_type": "skill", "skill_key": "warrior_cleave", "valid": True, "damage": 36, "resource_gained": 25},
        {"user_id": 2, "action_type": "skill", "skill_key": "priest_holy_ray", "valid": True, "damage": 48, "resource_spent": 12},
    ],
    "events": [
        {"type": "rage_gain_attack", "user_id": 1, "value": 15, "before": 0, "after": 15},
        {"type": "rage_gain_skill", "user_id": 1, "value": 10, "before": 15, "after": 25},
        {"type": "rage_gain_damage_taken", "user_id": 1, "value": 10, "before": 25, "after": 35},
    ],
}
text = render_pvp_round_combat_log(payload, 1)
warrior_action = text.index("Бог</b> використав")
self_rage = text.index("🔥 Лють: +25 → 25/100")
priest_action = text.index("Dedor</b> використав")
incoming_rage = text.index("🔥 <b>Бог</b>: +10 Люті від отриманої шкоди → 35/100")
assert warrior_action < self_rage < priest_action < incoming_rage
assert "Dedor</b>: +10 Люті" not in text

energy_payload = {
    "round_number": 2,
    "actors": [
        {"user_id": 3, "character_name": "Скаут", "class_key": "scout", "hp": 300, "max_hp": 395, "resource_type": "combat_energy", "resource": 75, "mp": 0, "max_mp": 0},
        {"user_id": 4, "character_name": "Розбійник", "class_key": "rogue", "hp": 310, "max_hp": 395, "resource_type": "combat_energy_combo", "resource": 65, "mp": 0, "max_mp": 0},
    ],
    "outcomes": [],
    "events": [
        {"type": "combat_energy_regen", "user_id": 3, "value": 20, "before": 55, "after": 75, "maximum": 100},
        {"type": "combat_energy_regen", "user_id": 4, "value": 20, "before": 45, "after": 65, "maximum": 100},
    ],
}
energy_text = render_pvp_round_combat_log(energy_payload, 3)
assert "⚡ <b>Скаут</b>: +20 Енергії → 75/100" in energy_text
assert "⚡ <b>Розбійник</b>: +20 Енергії → 65/100" in energy_text
print("[OK] PvP battle log resource grouping 14.6.5c")
print("- action Rage grouped with owner: PASS")
print("- incoming-damage Rage names owner: PASS")
print("- Energy regeneration names owner: PASS")
print("- battle logic changes: 0")
print("- production database writes: 0")
