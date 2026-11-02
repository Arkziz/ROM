#!/usr/bin/env python3
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = ['db_modules/connection.py', 'systems/admin_crystal_credit_system.py', 'systems/crystal_bag_expansion_system.py', 'systems/crystal_shop_system.py', 'systems/crystal_wallet_system.py', 'systems/fatigue_artifact_system.py', 'systems/inactivity_reminder_system.py', 'systems/item_id_allocator_system.py', 'systems/name_rune_system.py', 'systems/player_interaction_system.py', 'systems/player_rankings_system.py', 'systems/premium_item_policy_system.py', 'systems/profile_history_system.py', 'systems/refine_system.py', 'systems/timed_exp_bonus_system.py', 'systems/travel_system.py', 'systems/world_chronicle_system.py']
ALLOWLIST = {'systems/notifications.py': 1, 'systems/pvp_system.py': 2, 'systems/simulation/progression_economy_reporting.py': 1, 'systems/sqlite_connection_policy.py': 1}


def name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return (name(node.value) + "." + node.attr).strip(".")
    return ""

found = {}
paths = [ROOT / "db.py", ROOT / "main.py"]
for directory in ("db_modules", "systems", "handlers", "events", "migrations"):
    base = ROOT / directory
    if base.exists():
        paths.extend(base.rglob("*.py"))
for path in sorted({p.resolve() for p in paths if p.is_file()}):
    rel = path.relative_to(ROOT).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=rel)
    count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Call) and name(node.func) in {"sqlite3.connect", "_guild_sqlite3.connect"})
    if count:
        found[rel] = count
assert found == ALLOWLIST, (found, ALLOWLIST)
for rel in COHORT:
    source = (ROOT / rel).read_text(encoding="utf-8-sig")
    assert "from systems.sqlite_connection_policy import connect_runtime" in source, rel
    assert "connect_runtime(" in source, rel
policy = (ROOT / "systems/sqlite_connection_policy.py").read_text(encoding="utf-8-sig")
assert "journal_mode" not in policy.lower()
assert "PRAGMA foreign_keys=ON" in policy
assert "PRAGMA busy_timeout=" in policy
print("PASS: Stage 21.3.2 SQLite connection policy cohort and special-consumer allowlist")
