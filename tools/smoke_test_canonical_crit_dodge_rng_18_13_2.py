from __future__ import annotations
import ast
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
from data.player_combat_chances import *

class FixedRng:
    def __init__(self, value): self.value = value
    def random(self): return self.value

assert CRIT_MAX_CHANCE == CRIT_SOFT_CAP_ASYMPTOTE == 60.0
assert DODGE_MAX_CHANCE == DODGE_SOFT_CAP_ASYMPTOTE == 50.0
assert DODGE_MIN_CHANCE == 1.0
assert CRITICAL_DAMAGE_MULTIPLIER == 1.5
assert calculate_physical_crit_chance(10) == 5.0
assert calculate_physical_crit_chance(20) == 8.5
assert calculate_physical_crit_chance(50) == 19.0
assert math.isclose(calculate_physical_crit_chance(100), 31.264957264957264)
assert math.isclose(calculate_magical_crit_chance(125), 35.00371747211896)
assert calculate_physical_crit_chance(1000000) < 60.0
assert calculate_dodge_chance(10, 30) == 1.0
assert calculate_dodge_chance(30, 30) == 5.0
assert calculate_dodge_chance(70, 30) == 13.0
assert math.isclose(calculate_dodge_chance(155, 30), 24.64814814814815)
assert calculate_dodge_chance(1000000, 0) < 50.0
assert roll_chance(0.0, FixedRng(0.0)) is False
assert roll_chance(100.0, FixedRng(math.nextafter(1.0, 0.0))) is True
assert roll_chance(35.0, FixedRng(0.35)) is False
assert roll_chance(35.0, FixedRng(math.nextafter(0.35, 0.0))) is True
policy = (ROOT / "data/player_combat_chances.py").read_text(encoding="utf-8")
tree = ast.parse(policy)
for name in ("_calculate_crit_chance_with_soft_cap", "calculate_physical_crit_chance", "calculate_magical_crit_chance", "calculate_dodge_chance"):
    assert len([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]) == 1
crit = [calculate_physical_crit_chance(v / 10) for v in range(0, 100001)]
dodge = [calculate_dodge_chance(v / 10, 0) for v in range(-10000, 10001)]
assert all(a <= b for a, b in zip(crit, crit[1:])) and max(crit) < 60.0
assert all(a <= b for a, b in zip(dodge, dodge[1:])) and max(dodge) < 50.0
print("PASS: canonical 60%/50% soft caps, strict RNG and single-owner definitions")
