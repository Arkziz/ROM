from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def function_source(relative, name):
    text = (ROOT / relative).read_text(encoding="utf-8")
    tree = ast.parse(text)
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(nodes) == 1, (relative, name, len(nodes))
    return ast.get_source_segment(text, nodes[0]) or ""


def main():
    profile = function_source("handlers/profile.py", "build_stats_text")
    assert "physical_attack = get_attack(user_id)" in profile
    assert "magical_attack = get_magic_attack(user_id)" in profile
    assert "physical_attack = total_str" not in profile
    assert "magical_attack = total_int" not in profile

    attack_profile = function_source("db_modules/player.py", "get_player_attack_profile")
    assert attack_profile.count("get_attack(user_id)") == 1
    assert attack_profile.count("get_magic_attack(user_id)") == 1
    assert attack_profile.count("physical_stat_attack") >= 5
    assert attack_profile.count("magical_stat_attack") >= 2
    assert "stat_attack = total_str" not in attack_profile
    assert "stat_attack = total_int" not in attack_profile
    assert '"display_attack": physical_stat_attack' in attack_profile
    assert "display_attack = stat_attack + weapon_max" in attack_profile

    from systems.stat_system import calculate_physical_attack, calculate_magical_attack
    assert calculate_physical_attack("rogue", strength=22, dexterity=31) == 29
    assert calculate_physical_attack("scout", strength=10, dexterity=10) == 11
    assert calculate_physical_attack("warrior", strength=22, dexterity=31) == 22
    assert calculate_physical_attack("knight", strength=22, dexterity=31) == 22
    assert calculate_magical_attack("mage", intelligence=31) == 31
    assert calculate_magical_attack("priest", intelligence=31) == 31
    print("[PASS] profile parameters and attack-profile routes use canonical combat-stat APIs")


if __name__ == "__main__":
    main()
