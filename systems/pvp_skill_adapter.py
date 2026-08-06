from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[1]


class PvpSkillCatalogError(RuntimeError):
    pass


def load_production_pvp_skill_catalog() -> dict[str, tuple[dict[str, Any], ...]]:
    """Load the one canonical PvE catalog without importing Telegram handlers."""
    path = _ROOT / "handlers" / "combat.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assignments = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CLASS_SKILLS_V1" for t in node.targets):
            assignments.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "CLASS_SKILLS_V1":
            assignments.append(node.value)
    if len(assignments) != 1:
        raise PvpSkillCatalogError(f"CLASS_SKILLS_V1 assignments={len(assignments)}")
    catalog = ast.literal_eval(assignments[0])
    if not isinstance(catalog, dict):
        raise PvpSkillCatalogError("CLASS_SKILLS_V1 is not a dict")
    normalized = {str(cls): tuple(dict(skill) for skill in skills) for cls, skills in catalog.items()}
    if set(normalized) != {"warrior", "knight", "scout", "rogue", "mage", "priest"}:
        raise PvpSkillCatalogError("production class set changed")
    if sum(len(skills) for skills in normalized.values()) != 18:
        raise PvpSkillCatalogError("production skill count is not 18")
    return normalized


def get_production_pvp_skill(class_key: str, skill_key: str, catalog: Mapping[str, tuple[dict[str, Any], ...]] | None = None) -> dict[str, Any] | None:
    source = catalog or load_production_pvp_skill_catalog()
    return next((dict(skill) for skill in source.get(class_key, ()) if skill.get("key") == skill_key), None)
