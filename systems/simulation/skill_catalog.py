from __future__ import annotations
import ast
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

class SkillCatalogError(RuntimeError):
    pass

def load_production_skill_catalog(project_root: Path) -> Dict[str, List[Dict[str, Any]]]:
    path = Path(project_root) / "handlers" / "combat.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    candidates=[]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CLASS_SKILLS_V1":
                    candidates.append(ast.literal_eval(node.value))
    if len(candidates) != 1:
        raise SkillCatalogError(f"expected one CLASS_SKILLS_V1, found {len(candidates)}")
    catalog=candidates[0]
    required={"warrior","knight","scout","rogue","mage","priest"}
    if set(catalog) != required:
        raise SkillCatalogError(f"class catalog mismatch: {sorted(catalog)}")
    for class_key, skills in catalog.items():
        if len(skills) != 3:
            raise SkillCatalogError(f"{class_key} must have 3 skills")
        for skill in skills:
            for key in ("key","cost_type","cost","cooldown","damage_multiplier","attack_type"):
                if key not in skill:
                    raise SkillCatalogError(f"{class_key} skill missing {key}")
    return deepcopy(catalog)
