from pathlib import Path
from datetime import datetime
import ast
import py_compile

PATCH_NAME = "9_0_5_regen_system_extract"
MARKER = "# ✅ REFACTOR 9.0.5: REGEN SYSTEM FACADE"

REGEN_FUNCTION_CANDIDATES = [
    "init_hp_regen_system",
    "init_passive_regen_system",
    "process_passive_regeneration",
    "reset_hp_regen_timers_now",
    "apply_passive_hp_regen",
    "apply_passive_mp_regen",
    "process_hp_regeneration",
    "process_mp_regeneration",
    "get_hp_regen_status",
    "get_mp_regen_status",
]


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def get_defined_functions(text):
    tree = ast.parse(text)
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            result.append(node.name)
    return result


def write_regen_system(root):
    systems_dir = root / "systems"
    systems_dir.mkdir(exist_ok=True)
    target = systems_dir / "regen_system.py"

    if target.exists():
        make_backup(root, target)

    content = r
ROM Regen System
================

Refactor 9.0.5 compatibility module.

This module is intentionally conservative:
- db.py remains the public compatibility facade for handlers.
- legacy implementations are kept in db.py as _legacy_regen_v1_* references.
- this module delegates to those legacy implementations.

Important HP rules:
- dynamic max HP from equipment/refine must be respected;
- equipping/refining armor must not heal the player automatically;
- passive regeneration may heal up to dynamic max HP;
- if max HP decreases, current HP must be clamped to the new max.
