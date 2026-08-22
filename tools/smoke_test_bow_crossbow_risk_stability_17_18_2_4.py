#!/usr/bin/env python3
import ast
import random
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
if str(R) not in sys.path:
    sys.path.insert(0, str(R))

path = R / "systems/combat_system.py"
source = path.read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.18.2.4 BOW CROSSBOW RISK STABILITY BALANCE") == 1
assert 'subtype_multiplier = {"bow_2h": 0.95, "crossbow_2h": 1.10}' not in source

from systems.combat_system import calculate_player_attack

calls = []
old_randint = random.randint
old_uniform = random.uniform
try:
    def fake_randint(minimum, maximum):
        calls.append((minimum, maximum))
        return (minimum + maximum) // 2

    random.randint = fake_randint
    random.uniform = lambda a, b: 100.0
    common = dict(
        player_stat_attack=0,
        mob_def=0,
        dex=10,
        wis=10,
        level=1,
        weapon_min_damage=100,
        weapon_max_damage=200,
    )
    bow = calculate_player_attack(**common, weapon_subtype="bow_2h")
    crossbow = calculate_player_attack(**common, weapon_subtype="crossbow_2h")
    sword = calculate_player_attack(**common, weapon_subtype="sword_1h")
    unarmed = calculate_player_attack(
        player_stat_attack=10, mob_def=0, dex=10, wis=10, level=1,
        weapon_min_damage=0, weapon_max_damage=0, weapon_subtype=""
    )

    assert calls == [(105, 190), (85, 230), (100, 200)], calls
    assert bow["weapon_damage"] == 147, bow
    assert crossbow["weapon_damage"] == 157, crossbow
    assert sword["weapon_damage"] == 150, sword
    assert unarmed["weapon_damage"] == 0, unarmed
    assert bow["damage"] == 147 and crossbow["damage"] == 157
finally:
    random.randint = old_randint
    random.uniform = old_uniform

print("[PASS] Stage 17.18.2.4 bow/crossbow risk-stability contract")
