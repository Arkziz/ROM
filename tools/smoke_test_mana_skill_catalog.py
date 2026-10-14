#!/usr/bin/env python3
"""AST-based verifier for hybrid Mana metadata in CLASS_SKILLS_V1."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.mana_policy import calculate_mana_skill_cost, validate_mana_skill_definition

PROFILES = {
    "mage_fireball": ("mage", 20, 8, 7, None),
    "mage_thunder_spell": ("mage", 45, 15, 18, None),
    "mage_arcane_flow": ("mage", 0, 0, 0, 25),
    "priest_holy_ray": ("priest", 12, 6, 4, None),
    "priest_healing_blessing": ("priest", 30, 12, 10, None),
    "priest_purify_faith": ("priest", 20, 10, 8, 15),
}
VECTORS = {
    "mage_fireball": {170: 20, 300: 29, 600: 50, 1000: 78},
    "mage_thunder_spell": {170: 46, 300: 69, 600: 123, 1000: 195},
    "mage_arcane_flow": {170: 0, 300: 0, 600: 0, 1000: 0},
    "priest_holy_ray": {170: 13, 300: 18, 600: 30, 1000: 46},
    "priest_healing_blessing": {170: 29, 300: 42, 600: 72, 1000: 112},
    "priest_purify_faith": {170: 24, 300: 34, 600: 58, 1000: 90},
}


def load_catalog():
    """Load the literal catalog without importing Telegram handlers."""
    path = PROJECT_ROOT / "handlers" / "combat.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    assignments = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "CLASS_SKILLS_V1"
            for target in node.targets
        ):
            assignments.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "CLASS_SKILLS_V1"
        ):
            assignments.append(node.value)
    assert len(assignments) == 1, f"CLASS_SKILLS_V1 assignments={len(assignments)}"
    return ast.literal_eval(assignments[0])


def main():
    catalog = load_catalog()
    assert set(catalog) == {"warrior", "knight", "scout", "rogue", "mage", "priest"}
    assert sum(len(skills) for skills in catalog.values()) == 18
    found = {}
    for class_key in ("mage", "priest"):
        assert len(catalog[class_key]) == 3
        for skill in catalog[class_key]:
            key = skill["key"]
            assert key in PROFILES
            expected_class, legacy, flat, percent, restore = PROFILES[key]
            assert class_key == expected_class
            assert skill["cost_type"] == "mana"
            assert skill["cost"] == legacy, (key, "legacy cost changed")
            assert skill["mana_cost_flat"] == flat
            assert skill["mana_cost_max_mp_percent"] == percent
            if restore is None:
                assert "restore_max_mp_percent" not in skill
            else:
                assert skill["restore_max_mp_percent"] == restore
            validate_mana_skill_definition(skill)
            for max_mp, expected_cost in VECTORS[key].items():
                assert calculate_mana_skill_cost(skill, max_mp) == expected_cost
            found[key] = skill
    assert set(found) == set(PROFILES)

    # Physical classes remain outside the hybrid Mana contract.
    for class_key in ("warrior", "knight", "scout", "rogue"):
        for skill in catalog[class_key]:
            assert "mana_cost_flat" not in skill
            assert "mana_cost_max_mp_percent" not in skill
            assert "restore_max_mp_percent" not in skill

    print("[OK] Mana skill catalog smoke test - 6 hybrid profiles, 24 vectors, legacy-cost compatibility and physical-class isolation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
