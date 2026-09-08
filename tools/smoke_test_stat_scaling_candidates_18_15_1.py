from __future__ import annotations

import ast
import math
from pathlib import Path

from data.defense_policy import calculate_total_defense
from data.player_hp import calculate_base_max_hp
from data.stat_scaling import (
    CLASS_SCALING_CANDIDATES,
    SUPPORTED_CLASSES,
    calc_matk,
    calc_max_hp_parity,
    calc_mdef_parity,
    calc_patk,
    calc_pdef_parity,
    get_candidate,
    normalize_class_key,
    round_stat,
    validate_class_scaling,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "stat_scaling.py"

assert normalize_class_key(" Warrior ") == "warrior"
assert set(SUPPORTED_CLASSES) == {"warrior", "knight", "rogue", "scout", "mage", "priest"}
for name, candidate in CLASS_SCALING_CANDIDATES.items():
    validate_class_scaling(candidate)

stats = {"str": 20, "dex": 30, "int": 40, "wis": 50}
assert calc_patk("warrior", stats, "current_identity") == 20
assert calc_matk("mage", stats, "current_identity") == 40
assert calc_patk("warrior", stats, "candidate_c") == 40
assert calc_patk("knight", stats, "candidate_c") == 30
assert calc_patk("rogue", stats, "candidate_c") == 56
assert calc_patk("scout", stats, "candidate_c") == 53
assert calc_matk("mage", stats, "candidate_c") == 80
assert calc_matk("priest", stats, "candidate_c") == 89
assert calc_patk("unknown", stats, "candidate_c") == 20
assert calc_matk("unknown", stats, "candidate_c") == 40
assert round_stat(10.49) == 10 and round_stat(10.5) == 11

for bad in (True, "1", float("nan"), float("inf"), -1):
    try:
        calc_patk("warrior", {"str": bad}, "candidate_c")
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(f"invalid numeric value accepted: {bad!r}")

assert calc_max_hp_parity(1, 10, 0) == calculate_base_max_hp(1, 10)
assert calc_pdef_parity(17, 31) == int(calculate_total_defense(17, 31))
assert calc_mdef_parity(23, 37) == int(calculate_total_defense(23, 37))

text = SOURCE.read_text(encoding="utf-8")
tree = ast.parse(text)
for node in tree.body:
    if isinstance(node, ast.Import):
        assert all(not alias.name.startswith(("db", "systems")) for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module:
        assert not node.module.startswith(("db", "systems"))
assert "player_combat_chances" not in text
assert "pdef_sta" not in text and "mdef_wis" not in text
assert "sqlite3" not in text and "user_id" not in text and "inventory_id" not in text

try:
    CLASS_SCALING_CANDIDATES["candidate_c"] = {}
except TypeError:
    pass
else:
    raise AssertionError("candidate registry is mutable")

print("PASS: pure Stat System 2.0 candidate foundation; no runtime switch; HP/defense parity preserved")
