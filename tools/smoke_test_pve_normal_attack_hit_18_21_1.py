#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SYSTEM_SOURCE = (ROOT / "systems/combat_system.py").read_text(encoding="utf-8-sig")
HANDLER_SOURCE = (ROOT / "handlers/combat.py").read_text(encoding="utf-8-sig")
SYSTEM_TREE = ast.parse(SYSTEM_SOURCE)
HANDLER_TREE = ast.parse(HANDLER_SOURCE)
SYSTEM_FUNCS = {n.name: n for n in SYSTEM_TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert "calculate_player_hit_chance" in SYSTEM_FUNCS
assert "roll_player_normal_attack_hit" in SYSTEM_FUNCS
module = ast.Module(body=[SYSTEM_FUNCS["calculate_player_hit_chance"], SYSTEM_FUNCS["roll_player_normal_attack_hit"]], type_ignores=[])
ast.fix_missing_locations(module)
class FakeRandomModule:
 @staticmethod
 def randint(a, b): return a
ns = {"random": FakeRandomModule}
exec(compile(module, "hit_fixture", "exec"), ns)
chance = ns["calculate_player_hit_chance"]
roll = ns["roll_player_normal_attack_hit"]
assert chance(10, 10) == 95.0
assert chance(18, 10) == 99.0
assert chance(10, 1000) == 50.0
assert chance("bad", None) == 95.0
class Fixed:
 def __init__(self, value): self.value = value; self.calls = 0
 def randint(self, a, b): self.calls += 1; assert (a, b) == (1, 100); return self.value
hit_rng = Fixed(95); miss_rng = Fixed(96)
assert roll(10, 10, hit_rng)["hit"] is True and hit_rng.calls == 1
assert roll(10, 10, miss_rng)["hit"] is False and miss_rng.calls == 1
handlers = [n for n in ast.walk(HANDLER_TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "attack"]
assert len(handlers) == 1
attack_source = ast.get_source_segment(HANDLER_SOURCE, handlers[0]) or ""
assert "roll_player_normal_attack_hit" in attack_source
assert attack_source.index("roll_player_normal_attack_hit") < attack_source.index("calculate_player_attack")
assert 'player_attack_hit = bool(player_hit_result["hit"])' in attack_source
assert 'if player_attack_hit:' in attack_source
assert 'dmg = 0' in attack_source
assert 'is_player_crit = False' in attack_source
assert 'mob["hp"] -= dmg' in attack_source
assert attack_source.index('if player_attack_hit:') < attack_source.index('mob["hp"] -= dmg')
assert 'resource_attack_text = add_rage_for_player_attack(mob)' in attack_source
assert '💨 ПРОМАХ!' in attack_source
# Skills are deliberately outside Stage 18.21.1 scope.
skill_handlers = [n for n in ast.walk(HANDLER_TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "combat_use_skill_callback"]
assert len(skill_handlers) == 1
skill_source = ast.get_source_segment(HANDLER_SOURCE, skill_handlers[0]) or ""
assert "roll_player_normal_attack_hit" not in skill_source
assert "systems.pvp_" not in attack_source
print("[PASS] Stage 18.21.1 normal-hit boundaries, hit-before-crit, miss invariants and skill/PvP isolation")
