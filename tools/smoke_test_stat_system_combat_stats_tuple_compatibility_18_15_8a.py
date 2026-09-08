from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER = ROOT / "systems" / "player_system.py"


def main():
    text = PLAYER.read_text(encoding="utf-8")
    tree = ast.parse(text)
    names = ("get_attack", "get_magic_attack", "get_physical_defense", "get_magic_defense")
    for name in names:
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
        assert len(functions) == 1, (name, len(functions))
        source = ast.get_source_segment(text, functions[0]) or ""
        assert "get_player_stats(user_id)[:5]" in source, name

    six_values = (22, 31, 12, 18, 22, 3)
    strength, dexterity, intelligence, wisdom, stamina = six_values[:5]
    assert (strength, dexterity, intelligence, wisdom, stamina) == (22, 31, 12, 18, 22)

    from systems.stat_system import (
        calculate_magical_attack,
        calculate_magical_defense,
        calculate_physical_attack,
        calculate_physical_defense,
    )
    assert calculate_physical_attack("rogue", strength=strength, dexterity=dexterity) == 29
    assert calculate_magical_attack("rogue", intelligence=intelligence) == 2
    assert calculate_physical_defense(equipment_pdef=10, stamina=stamina) == 17
    assert calculate_magical_defense(equipment_mdef=10, wisdom=wisdom) == 16
    print("[PASS] six-value get_player_stats compatibility; first five stat positions preserved")


if __name__ == "__main__":
    main()
