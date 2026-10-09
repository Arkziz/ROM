#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained verifier for Stage 20.2.3 PvP/simulator basic-attack parity."""
from __future__ import annotations
import ast
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.stat_system import resolve_basic_attack_type
EXPECTED={"warrior":"physical","knight":"physical","scout":"physical","rogue":"physical","mage":"magical","priest":"magical"}
assert {key:resolve_basic_attack_type(key) for key in EXPECTED}==EXPECTED
files={name:(ROOT/name).read_text(encoding="utf-8-sig") for name in (
 "systems/pvp_round_engine.py","systems/pvp_battle_factory.py",
 "systems/simulation/combat_actor_stats.py","systems/simulation/pve_battle.py")}
for name,source in files.items():ast.parse(source,filename=name);compile(source,name,"exec")
assert "from systems.stat_system import resolve_basic_attack_type" in files["systems/pvp_round_engine.py"]
assert 'resolve_basic_attack_type(actor.class_key)' in files["systems/pvp_round_engine.py"]
assert '("magical" if actor.class_key in {"mage", "priest"} else "physical")' not in files["systems/pvp_round_engine.py"]
assert '(skill or {}).get("attack_type") or resolve_basic_attack_type(actor.class_key)' in files["systems/pvp_round_engine.py"]
assert "from systems.stat_system import resolve_basic_attack_type" in files["systems/pvp_battle_factory.py"]
assert "attack_type = resolve_basic_attack_type(class_key)" in files["systems/pvp_battle_factory.py"]
assert 'attack_profile.get("attack_type") or "physical"' not in files["systems/pvp_battle_factory.py"]
assert "from systems.stat_system import" in files["systems/simulation/combat_actor_stats.py"]
assert "resolve_basic_attack_type(character_class)" in files["systems/simulation/combat_actor_stats.py"]
assert 'attack_type="magical" if mana else "physical"' not in files["systems/simulation/combat_actor_stats.py"]
assert "from systems.stat_system import resolve_basic_attack_type" in files["systems/simulation/pve_battle.py"]
assert "MAGIC_CLASSES=" not in files["systems/simulation/pve_battle.py"]
assert "kind=resolve_basic_attack_type(class_key)" in files["systems/simulation/pve_battle.py"]
# Skill routes remain skill-owned; only basic attacks consume canonical class policy.
assert 'skill["attack_type"]' in files["systems/simulation/pve_battle.py"]
assert '(skill or {}).get("attack_type")' in files["systems/pvp_round_engine.py"]
# Basic attacks remain cost zero in PvP and do not debit simulator resources.
assert '"skill": None, "cost": 0, "combo_spent": 0' in files["systems/pvp_round_engine.py"]
print("PASS")
