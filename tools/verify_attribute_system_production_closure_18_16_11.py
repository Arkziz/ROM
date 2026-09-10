#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only full integration verifier for ROM Stage 18.16."""
from __future__ import annotations
import importlib, json, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_16_11_attribute_system_production_closure.json"

REQUIRED_TESTS = (
    "tools/smoke_test_level_up_attribute_points_18_16_2.py",
    "tools/smoke_test_attribute_allocation_system_18_16_3.py",
    "tools/smoke_test_effective_attribute_integration_18_16_4.py",
    "tools/smoke_test_profile_attribute_allocation_ui_18_16_5.py",
    "tools/smoke_test_profile_attribute_ui_navigation_18_16_5a.py",
    "tools/smoke_test_profile_attribute_ui_text_18_16_5b.py",
    "tools/smoke_test_notification_resource_integration_18_16_5d.py",
    "tools/smoke_test_level_up_attribute_point_messages_18_16_6.py",
    "tools/smoke_test_existing_character_attribute_point_policy_18_16_7.py",
    "tools/smoke_test_attribute_respec_domain_18_16_8.py",
    "tools/smoke_test_new_path_sphere_class_change_18_16_9.py",
    "tools/smoke_test_class_change_resource_getter_fix_18_16_9a.py",
    "tools/smoke_test_rebirth_sphere_inventory_ui_18_16_10.py",
    "tools/smoke_test_sphere_stack_and_category_fix_18_16_10a.py",
    "tools/smoke_test_rebirth_sphere_economic_policy_18_16_10b.py",
    "tools/smoke_test_sphere_inventory_card_style_18_16_10c.py",
    "tools/smoke_test_rebirth_sphere_stack_limit_18_16_10d.py",
    "tools/smoke_test_rebirth_sphere_drop_18_16_10f.py",
)
# Historical point-in-time tests excluded from closure:
# - 18.16.1 asserted every ledger field remained zero immediately after foundation.
#   Policy C, level rewards and player allocation intentionally superseded that state.
# - 18.16.10e asserted that no Rebirth Sphere production drop rule existed.
#   Stage 18.16.10f intentionally superseded that state.
SUPERSEDED_TESTS = (
    "tools/smoke_test_attribute_schema_foundation_18_16_1.py",
    "tools/smoke_test_rebirth_sphere_distribution_audit_18_16_10e.py",
)
REQUIRED_IMPORTS = (
    "systems.attribute_allocation_system",
    "systems.attribute_respec_system",
    "systems.stat_system",
    "systems.player_system",
    "systems.character_system",
    "systems.drop_system",
    "systems.reward_system",
    "handlers.profile",
    "handlers.inventory",
)

def sha(path):
    return __import__("hashlib").sha256(path.read_bytes()).hexdigest()

def db_snapshot():
    conn = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        required_columns = {
            "free_attribute_points", "total_attribute_points_earned",
            "allocated_strength", "allocated_dexterity", "allocated_intelligence",
            "allocated_wisdom", "allocated_stamina", "attribute_points_migrated_at",
            "pending_class_change_inventory_id",
        }
        users = conn.execute("""SELECT user_id,level,free_attribute_points,total_attribute_points_earned,
            allocated_strength,allocated_dexterity,allocated_intelligence,allocated_wisdom,allocated_stamina
            FROM users ORDER BY user_id""").fetchall()
        invariant_errors = []
        for row in users:
            user_id, level, free, earned, strength, dexterity, intelligence, wisdom, stamina = row
            allocated = sum(int(value or 0) for value in (strength,dexterity,intelligence,wisdom,stamina))
            if int(earned or 0) != int(free or 0) + allocated:
                invariant_errors.append({"user_id":user_id,"level":level,"free":free,"earned":earned,"allocated":allocated})
        items = conn.execute("SELECT id,name,type,category,max_stack,sell_price FROM items WHERE id IN (501,504) ORDER BY id").fetchall()
        migrations = [row[0] for row in conn.execute("SELECT migration_name FROM schema_migrations ORDER BY migration_name")]
        audit_count = conn.execute("SELECT COUNT(*) FROM attribute_respec_events").fetchone()[0]
        return {
            "quick_check": conn.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_violations": conn.execute("PRAGMA foreign_key_check").fetchall(),
            "required_columns_missing": sorted(required_columns - columns),
            "users_checked": len(users),
            "ledger_invariant_errors": invariant_errors,
            "items": items,
            "migrations": migrations,
            "attribute_respec_events": audit_count,
            "total_changes": conn.total_changes,
        }
    finally:
        conn.close()

def main():
    before_sha = sha(DB)
    db = db_snapshot()
    results = []
    missing = [rel for rel in REQUIRED_TESTS if not (ROOT/rel).is_file()]
    if missing:
        raise RuntimeError(f"Required Stage 18.16 smoke tests missing: {missing}")
    for rel in REQUIRED_TESTS:
        proc = subprocess.run([sys.executable, str(ROOT/rel)], cwd=ROOT, text=True, capture_output=True)
        results.append({"test":rel,"returncode":proc.returncode,"stdout":proc.stdout[-4000:],"stderr":proc.stderr[-4000:]})
        if proc.returncode:
            raise RuntimeError(f"Stage 18.16 smoke test failed: {rel}")
    imports = []
    for name in REQUIRED_IMPORTS:
        importlib.import_module(name)
        imports.append(name)
    from data.drop_tables import DROP_RULES_BY_ID, CENTRAL_DROP_VICTORY_RULE_ORDER
    from data.rebirth_sphere_policy import get_sphere_economic_policy
    from systems.drop_system import get_victory_drop_plan, validate_drop_tables
    from systems.premium_item_policy_system import PREMIUM_ITEM_POLICY, DENIED_TRANSFER_ITEM_IDS
    rule = DROP_RULES_BY_ID.get("rebirth_sphere")
    if not rule:
        raise RuntimeError("rebirth_sphere drop rule missing")
    expected_chances = {"normal":{"chance":0.0002},"elite":{"chance":0.001},"boss":{"chance":0.01}}
    if rule.get("enemy") != expected_chances or rule.get("item_id") != 504 or not rule.get("production_enabled"):
        raise RuntimeError(f"rebirth_sphere drop contract drifted: {rule}")
    if tuple(CENTRAL_DROP_VICTORY_RULE_ORDER) != tuple(get_victory_drop_plan()) or get_victory_drop_plan()[-1] != "rebirth_sphere":
        raise RuntimeError("central victory plan drifted")
    if not validate_drop_tables()["success"]:
        raise RuntimeError("central drop schema invalid")
    new_path = get_sphere_economic_policy(501)
    rebirth = get_sphere_economic_policy(504)
    policy_ok = (
        501 in PREMIUM_ITEM_POLICY and 501 in DENIED_TRANSFER_ITEM_IDS
        and 504 not in PREMIUM_ITEM_POLICY and 504 not in DENIED_TRANSFER_ITEM_IDS
        and new_path["mob_drop_eligible"] is False and new_path["crystal_shop_eligible"] is True
        and rebirth["mob_drop_eligible"] is True and rebirth["crystal_shop_eligible"] is False
        and rebirth["tradeable"] is True and rebirth["auctionable"] is True
    )
    after_sha = sha(DB)
    verdict = (
        db["quick_check"] == "ok" and not db["foreign_key_violations"]
        and not db["required_columns_missing"] and not db["ledger_invariant_errors"]
        and db["total_changes"] == 0 and before_sha == after_sha and policy_ok
    )
    report = {
        "stage":"18.16.11",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"PASS" if verdict else "FAIL",
        "production_mutation":False,
        "database_sha256_before":before_sha,
        "database_sha256_after":after_sha,
        "database":db,
        "smoke_tests":results,
        "smoke_test_count":len(results),
        "superseded_tests_not_run":list(SUPERSEDED_TESTS),
        "imports":imports,
        "sphere_policy_ok":policy_ok,
        "drop_rule":rule,
        "victory_plan":list(get_victory_drop_plan()),
        "known_nuances":[
            "The Stage 18.16.1 foundation smoke test is superseded because it requires every ledger value to remain zero; closure validates schema and the live ledger invariant directly.",
            "The Stage 18.16.10e audit smoke test is superseded because production drop is now enabled.",
            "Natural drop frequency is too low for practical manual hit testing; deterministic boundary tests are authoritative.",
            "Rebirth Sphere NPC sell_price remains 0.0; player auction and direct trade are supported.",
        ],
    }
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    if not verdict:
        raise RuntimeError("Stage 18.16 closure invariants failed")
    print(json.dumps({"status":"PASS","tests":len(results),"users":db["users_checked"],"db_unchanged":before_sha==after_sha},ensure_ascii=False))

if __name__ == "__main__":
    main()
