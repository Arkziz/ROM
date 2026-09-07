from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from data.defense_policy import (
    DAMAGE_DEFENSE_COEFFICIENT,
    DEFENSE_STAT_COEFFICIENT,
    MINIMUM_DAMAGE,
    calculate_damage_after_defense,
    calculate_stat_defense,
    calculate_total_defense,
)

assert DEFENSE_STAT_COEFFICIENT == 0.35
assert DAMAGE_DEFENSE_COEFFICIENT == 0.5
assert MINIMUM_DAMAGE == 1
assert calculate_stat_defense(10) == 3.5
assert calculate_stat_defense(20) == 7.0
assert calculate_stat_defense(-10) == 0.0
assert calculate_total_defense(5, 20) == 12.0
assert calculate_total_defense(5, 20) == calculate_total_defense(5, 20)
assert calculate_damage_after_defense(20, 10) == 15.0
assert calculate_damage_after_defense(5, 100) == 1.0

player_text = (ROOT / "systems" / "player_system.py").read_text(encoding="utf-8")
player_tree = ast.parse(player_text)
physical = [n for n in player_tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_physical_defense"]
magical = [n for n in player_tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_magic_defense"]
assert len(physical) == 2
assert len(magical) == 2
assert "calculate_total_defense(item_pdef, stats[4])" in (ast.get_source_segment(player_text, physical[-1]) or "")
assert "calculate_total_defense(item_mdef, stats[3])" in (ast.get_source_segment(player_text, magical[-1]) or "")
assert "int(int(item_pdef or 0) + int(stats[4]) * 0.2)" not in player_text
assert "int(int(item_mdef or 0) + int(stats[3]))" not in player_text

sim_text = (ROOT / "systems" / "simulation" / "combat_actor_stats.py").read_text(encoding="utf-8")
assert 'calculate_total_defense(item_pdef, stats["sta"])' in sim_text
assert 'calculate_total_defense(item_mdef, stats["wis"])' in sim_text

combat_text = (ROOT / "systems" / "combat_system.py").read_text(encoding="utf-8")
assert "mob_attack - (defense * 0.5)" in combat_text
assert "if damage < 1:" in combat_text

print("PASS: symmetric PDEF/MDEF K=0.35; item defense preserved; damage coefficient unchanged")
