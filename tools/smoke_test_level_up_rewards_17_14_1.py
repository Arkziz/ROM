#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

before = sha256(DB)
for rel in ("systems/player_system.py", "systems/level_up_reward_system.py", "handlers/combat.py", "systems/contract_system.py"):
    source = (ROOT / rel).read_text(encoding="utf-8")
    ast.parse(source)
    assert source.count("ROM 17.14.1 LEVEL UP REWARDS") == 1

from systems.level_up_reward_system import calculate_level_rewards
single = calculate_level_rewards(4, 5)
assert single["gold"] == 150
assert single["health_potions"] == 3
assert single["simple_extractors"] == 1
assert single["crystals"] == 0
multi = calculate_level_rewards(4, 7)
assert multi["reached_levels"] == [5, 6, 7]
assert multi["milestone_levels"] == [5]
assert multi["gold"] == 280
assert multi["health_potions"] == 5
assert multi["simple_extractors"] == 1
assert calculate_level_rewards(7, 7)["gold"] == 0

player = (ROOT / "systems/player_system.py").read_text(encoding="utf-8")
player_tree = ast.parse(player)
add_exp_nodes = [
    node for node in player_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "add_exp"
]
assert len(add_exp_nodes) >= 2
authoritative_add_exp = ast.get_source_segment(player, add_exp_nodes[-1]) or ""
assert 'db.conn.execute("BEGIN IMMEDIATE")' in authoritative_add_exp
assert '"old_level": old_level' in authoritative_add_exp
assert '"reached_levels": reached_levels' in authoritative_add_exp
assert authoritative_add_exp.count("db.conn.commit()") == 1
assert authoritative_add_exp.count("db.conn.rollback()") >= 2
reward = (ROOT / "systems/level_up_reward_system.py").read_text(encoding="utf-8")
assert "UNIQUE(user_id, reached_level)" in reward
assert "RUNE_EXTRACTOR_ITEM_ID" in reward
assert "HEALTH_POTION_ITEM_ID = 201" in reward
assert "crystal_quantity" in reward
assert "commit=False" in reward
assert "ROLLBACK TO" in reward
assert sha256(DB) == before
print("[PASS] Stage 17.14.1 level-up reward contract")
