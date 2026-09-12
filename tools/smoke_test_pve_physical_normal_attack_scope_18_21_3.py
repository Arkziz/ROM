#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
HANDLER_SOURCE = (ROOT / "handlers/combat.py").read_text(encoding="utf-8-sig")
SYSTEM_SOURCE = (ROOT / "systems/combat_system.py").read_text(encoding="utf-8-sig")
HANDLER_TREE = ast.parse(HANDLER_SOURCE)
SYSTEM_TREE = ast.parse(SYSTEM_SOURCE)
attacks = [n for n in ast.walk(HANDLER_TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "attack"]
assert len(attacks) == 1
attack_source = ast.get_source_segment(HANDLER_SOURCE, attacks[0]) or ""
assert 'normal_attack_uses_hit_roll = attack_profile["attack_type"] == "physical"' in attack_source
assert 'if normal_attack_uses_hit_roll:' in attack_source
assert 'player_hit_result = roll_player_normal_attack_hit(' in attack_source
assert 'player_attack_hit = True' in attack_source
assert 'if player_attack_hit:' in attack_source
assert '💨 ПРОМАХ!' in attack_source
assert attack_source.index('if normal_attack_uses_hit_roll:') < attack_source.index('if player_attack_hit:')
# DEX roll remains canonical for physical normal attacks.
physical_branch = attack_source.split('if normal_attack_uses_hit_roll:', 1)[1].split('if player_attack_hit:', 1)[0]
assert 'player_dex=dex_' in physical_branch
assert 'mob_dex=mob.get("dex", 0)' in physical_branch
# Magical normal attacks bypass the DEX hit roll and continue to damage/crit calculation.
assert 'else:\n            player_hit_result = None\n            player_attack_hit = True' in attack_source
# Skills remain outside this mutation.
skills = [n for n in ast.walk(HANDLER_TREE) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "combat_use_skill_callback"]
assert len(skills) == 1
skill_source = ast.get_source_segment(HANDLER_SOURCE, skills[0]) or ""
assert "roll_player_normal_attack_hit" not in skill_source
assert "normal_attack_uses_hit_roll" not in skill_source
# Approved Stage 18.21.1 formula remains unchanged.
funcs = {n.name: n for n in SYSTEM_TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert "calculate_player_hit_chance" in funcs
hit_source = ast.get_source_segment(SYSTEM_SOURCE, funcs["calculate_player_hit_chance"]) or ""
assert "95.0" in hit_source and "0.5" in hit_source and "50.0" in hit_source and "99.0" in hit_source
assert "systems.pvp_" not in attack_source
print("[PASS] Stage 18.21.3 physical-only normal hit scope; magical normal and skills remain guaranteed-hit")
