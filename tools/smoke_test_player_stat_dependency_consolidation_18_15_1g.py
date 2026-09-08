from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER = ROOT / "systems" / "player_system.py"
EQUIPMENT = ROOT / "systems" / "equipment_system.py"


def top_level_counts(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    counts = {}
    definitions = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts[node.name] = counts.get(node.name, 0) + 1
            definitions[node.name] = node
    return counts, definitions, tree


player_counts, player_defs, player_tree = top_level_counts(PLAYER)
equipment_counts, equipment_defs, equipment_tree = top_level_counts(EQUIPMENT)
for name in ("get_player_stats", "get_attack", "get_magic_attack", "get_physical_defense", "get_magic_defense"):
    assert player_counts.get(name) == 1, (name, player_counts.get(name))
for name in ("get_item_bonuses", "get_equipped_item_defenses"):
    assert equipment_counts.get(name) == 1, (name, equipment_counts.get(name))

player_text = PLAYER.read_text(encoding="utf-8")
assert "_RUNE_STATS_BASE_GET_PLAYER_STATS_10_7_0" not in player_text
stats = player_defs["get_player_stats"]
loads = {node.id for node in ast.walk(stats) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
assert "_player_base_row_9_0_12g" in loads
assert "_player_combat_db_9_0_12g" in loads
assert "get_equipped_rune_stat_totals" in loads

# The cleanup scope must not touch HP/MP/progression duplicate families.
assert player_counts.get("get_current_hp_raw") == 3
assert player_counts.get("get_current_hp") == 3
assert player_counts.get("set_current_hp") == 3
assert player_counts.get("add_exp") == 2

code = compile(ast.Module(body=[stats], type_ignores=[]), str(PLAYER), "exec")
namespace = {
    "_player_base_row_9_0_12g": lambda user_id: (10, 20, 30, 40, 50, 6),
    "_player_combat_db_9_0_12g": lambda: type("DB", (), {"get_item_bonuses": lambda self, user_id: (1, 2, 3, 4, 5)})(),
}
exec(code, namespace)
import systems.rune_system as rune_system
original = rune_system.get_equipped_rune_stat_totals
try:
    rune_system.get_equipped_rune_stat_totals = lambda user_id: {"str": 6, "dex": 7, "int": 8, "wis": 9, "sta": 10}
    assert namespace["get_player_stats"](123) == (17, 29, 41, 53, 65, 6)
finally:
    rune_system.get_equipped_rune_stat_totals = original

print("PASS: one canonical stat API each; item+rune totals exactly once; HP/MP/progression cleanup excluded")
