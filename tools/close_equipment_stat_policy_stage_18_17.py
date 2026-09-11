#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained production closure verifier for ROM Stage 18.17."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_17_9_equipment_stat_policy_production_closure.json"
MD = ROOT / "MD/STAGE_18_17_EQUIPMENT_STAT_POLICY_PRODUCTION_CLOSURE.md"

PRODUCTION_FILES = (
    "data/equipment_stat_policy.py",
    "data/equipment_profiles.py",
    "data/stat_system_config.py",
    "db_modules/generated_equipment.py",
    "db_modules/shop.py",
    "systems/dynamic_equipment_system.py",
)

MAINTAINED_TESTS = (
    "tools/smoke_test_class_aware_equipment_stat_policy_18_17_1.py",
    "tools/smoke_test_class_aware_generated_equipment_18_17_2.py",
    "tools/smoke_test_shop_class_aware_random_import_18_17_2a.py",
    "tools/verify_equipment_drop_shop_parity_18_17_3.py",
    "tools/smoke_test_legacy_class_shop_canonical_adapter_18_17_6.py",
    "tools/verify_dynamic_equipment_behavioral_parity_18_17_7.py",
    "tools/smoke_test_dynamic_equipment_thin_delegate_18_17_8.py",
)

EXPECTED_COMMITS = (
    "bf01dfa4ac6e9ae53fa7ffb0d735eba6a7dfbf43",
    "8d50b75909356654e1f622437bc3b3e0ce034869",
    "c1d38bb734656f0c047126bf9cc6ebab976da47e",
    "6ab4c0dcb94fdc549d57ba84130421d6a678a61e",
    "6526eb94916b4cc0022581d3214e8fca311dda3a",
    "38d8747b27bfd46c285df763ffcf13951fd1d04c",
    "70a234d5933fc1000afa9d84bef3da123caa709a",
    "a582839ed2391068c79ed1e8537767ddf587f9a4",
    "4fb999cde2f541c1fde4b0587b67f2e44f061906",
    "30cc7d362c5ecf3bb334ced3309e3c99e60681c8",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            "Command failed: " + " ".join(command) + "\n" + result.stdout + result.stderr
        )
    return {"command": command, "returncode": result.returncode, "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:]}


def database_check():
    before = sha(DB)
    conn = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        result = {
            "quick_check": conn.execute("PRAGMA quick_check").fetchone()[0],
            "foreign_key_violations": conn.execute("PRAGMA foreign_key_check").fetchall(),
            "total_changes": conn.total_changes,
        }
    finally:
        conn.close()
    result.update(sha256_before=before, sha256_after=sha(DB))
    result["unchanged"] = result["sha256_before"] == result["sha256_after"]
    return result


def structural_contracts():
    from data.equipment_stat_policy import (
        CLASS_ARMOR_TYPES,
        CLASS_MAIN_HAND_SUBTYPES,
        CLASS_OFF_HAND_SUBTYPES,
        CLASS_STAT_WEIGHTS,
        get_allowed_equipment_stats,
        validate_equipment_stat_policy,
    )
    import db_modules.generated_equipment as canonical
    import db_modules.shop as shop
    from systems import dynamic_equipment_system as compatibility

    classes = {"warrior", "knight", "scout", "rogue", "mage", "priest"}
    assert validate_equipment_stat_policy() == ()
    assert set(CLASS_STAT_WEIGHTS) == classes
    assert set(CLASS_ARMOR_TYPES) == classes
    assert CLASS_ARMOR_TYPES == {
        "mage": "cloth", "priest": "cloth", "scout": "leather",
        "rogue": "leather", "warrior": "chain", "knight": "plate",
    }
    assert get_allowed_equipment_stats("knight", "off_hand", item_subtype="shield") == ("sta", "str")
    assert set(get_allowed_equipment_stats("warrior", "jewelry")) <= {"str", "dex", "sta"}
    assert set(get_allowed_equipment_stats("mage", "jewelry")) <= {"int", "wis", "sta"}
    assert CLASS_MAIN_HAND_SUBTYPES["scout"] == ("bow_2h", "crossbow_2h")
    assert CLASS_OFF_HAND_SUBTYPES["scout"] == ()

    delegates = (
        "add_primary_stat_to_stats", "add_stat_value",
        "apply_armor_type_defense_profile_to_stats",
        "apply_armor_type_primary_stat_profile_to_stats",
        "clear_primary_stat_bonuses", "generate_dynamic_equipment_stats",
        "get_dynamic_armor_name", "get_dynamic_sell_price",
        "get_dynamic_stat_value", "get_dynamic_weapon_name",
        "get_existing_primary_stat_budget", "get_profile_for_generated_item",
        "get_random_main_hand_profile", "get_random_off_hand_profile",
        "init_dynamic_equipment_system", "normalize_equipment_restriction_value",
        "pick_weighted_stat",
    )
    for name in delegates:
        assert inspect.signature(getattr(canonical, name)) == inspect.signature(getattr(compatibility, name))

    dynamic_source = (ROOT / "systems/dynamic_equipment_system.py").read_text(encoding="utf-8-sig")
    shop_source = (ROOT / "db_modules/shop.py").read_text(encoding="utf-8-sig")
    generator_source = (ROOT / "db_modules/generated_equipment.py").read_text(encoding="utf-8-sig")
    ast.parse(dynamic_source)
    ast.parse(shop_source)
    ast.parse(generator_source)
    assert "from systems.dynamic_equipment_system import generate_equipment_item" not in shop_source
    assert "redistribute_primary_stat_budget(" in shop_source
    assert generator_source.count("redistribute_primary_stat_budget(") == 2
    assert "systems.dynamic_equipment_system" not in generator_source
    for forbidden in ("sqlite3", "cursor", "conn", "random.", "create_generated_equipment_item"):
        assert forbidden not in dynamic_source

    offers = shop.generate_class_shop_equipment("priest", 8)
    assert offers and all(row["target_class"] == "priest" for row in offers)
    assert callable(shop.populate_class_shop_for_user)

    return {
        "classes": sorted(classes),
        "armor_types": dict(CLASS_ARMOR_TYPES),
        "knight_shield": list(get_allowed_equipment_stats("knight", "off_hand", item_subtype="shield")),
        "delegated_functions": len(delegates),
        "legacy_missing_symbol_removed": True,
        "canonical_item_creation_owner": "db_modules/generated_equipment.py",
        "canonical_policy_owner": "data/equipment_stat_policy.py",
        "thin_compatibility_module": "systems/dynamic_equipment_system.py",
    }


def commit_check():
    rows = []
    for commit_hash in EXPECTED_COMMITS:
        result = subprocess.run(
            ["git", "cat-file", "-e", commit_hash + "^{commit}"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        rows.append({"hash": commit_hash, "present": result.returncode == 0})
    if not all(row["present"] for row in rows):
        raise RuntimeError("One or more Stage 18.17 commits are missing")
    return rows


def main():
    for relative in PRODUCTION_FILES + MAINTAINED_TESTS:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Required closure file missing: {relative}")
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8-sig"))

    commands = []
    commands.append(run([sys.executable, "-m", "py_compile", *[str(ROOT / path) for path in PRODUCTION_FILES + MAINTAINED_TESTS]]))
    structure = structural_contracts()
    for relative in MAINTAINED_TESTS:
        commands.append(run([sys.executable, str(ROOT / relative)]))

    parity = json.loads((ROOT / "reports/stage_18_17_3_equipment_drop_shop_parity.json").read_text(encoding="utf-8"))
    behavior = json.loads((ROOT / "reports/stage_18_17_7_dynamic_equipment_behavioral_fixtures.json").read_text(encoding="utf-8"))
    assert parity["status"] == "PASS" and parity["matrix_rows"] == 58 and parity["samples_per_row"] == 200
    assert parity["routes"]["purchase_reroll"] is False
    assert behavior["status"] == "PASS" and behavior["behavioral_parity"] is True and behavior["total_fixtures"] == 1950

    commits = commit_check()
    database = database_check()
    assert database["quick_check"] == "ok"
    assert database["foreign_key_violations"] == []
    assert database["total_changes"] == 0
    assert database["unchanged"] is True

    report = {
        "stage": "18.17.9",
        "status": "CLOSED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_mutation": False,
        "manual_acceptance": {
            "status": "PASS",
            "reported_by_user": True,
            "scenarios": [
                "base equipment shop opened after thin delegate consolidation",
                "weapon, armor, jewelry and off-hand previews worked",
                "class-appropriate stats verified with multiple classes",
                "preview and purchased item remained consistent",
                "inventory, comparison, equip, PvE and restart worked without traceback",
            ],
        },
        "structure": structure,
        "class_stat_weights": {
            "warrior": {"str": 60, "sta": 30, "dex": 10},
            "knight": {"sta": 50, "str": 45, "dex": 5},
            "scout": {"str": 45, "dex": 45, "sta": 10},
            "rogue": {"dex": 60, "str": 30, "sta": 10},
            "mage": {"int": 65, "wis": 25, "sta": 10},
            "priest": {"int": 50, "wis": 40, "sta": 10},
        },
        "invariants": {
            "existing_generated_items_migrated": False,
            "new_class_aware_drop_enabled": True,
            "new_base_shop_preview_class_aware": True,
            "shop_purchase_reroll": False,
            "rarity_multipliers_changed": False,
            "weapon_damage_changed": False,
            "armor_defense_identity_changed": False,
            "bow_crossbow_identity_preserved": True,
            "knight_shield_stats": ["sta", "str"],
            "wal_shm_manipulated": False,
        },
        "verification": {
            "maintained_tests": list(MAINTAINED_TESTS),
            "commands": commands,
            "drop_shop_matrix_rows": 58,
            "drop_shop_samples": 11600,
            "behavioral_fixtures": 1950,
            "commits": commits,
        },
        "database": database,
        "known_nuances": [
            "The class-aware policy applies to newly generated class-aware loot and new base-shop previews; existing generated items are not rewritten.",
            "Unrestricted loot remains unrestricted when class_aware_chance selects the random branch.",
            "Selection weights guide which primary stats receive existing generated stat chunks; they do not change the total stat budget.",
            "The legacy class-shop public signatures remain as read-only compatibility catalog adapters and do not populate items or previews.",
            "systems.dynamic_equipment_system remains import-compatible but delegates calculations to db_modules.generated_equipment.",
        ],
        "superseded_tests": [
            {
                "stage": "18.17.0",
                "reason": "Point-in-time audit described the pre-mutation stat mismatch and is retained as historical evidence, not a closure invariant.",
            },
            {
                "stage": "18.17.4",
                "reason": "Point-in-time compatibility audit reported duplicates and a missing legacy symbol that were intentionally resolved in 18.17.6 and 18.17.8.",
            },
            {
                "stage": "18.17.5",
                "reason": "Point-in-time legacy reachability audit justified the canonical adapter and is not rerun as a current broken-route assertion.",
            },
        ],
        "next_stage": "18.18 according to the current roadmap",
    }

    REPORT.parent.mkdir(exist_ok=True)
    MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Stage 18.17: Class-aware Equipment Stat Policy Production Closure",
        "",
        "**Status:** CLOSED",
        "**Manual acceptance:** PASS",
        "**Production database migration:** none",
        "",
        "## Objective",
        "",
        "Stage 18.17 makes newly generated equipment class-aware across mob loot and the base equipment shop while preserving armor defense identity, rarity budgets, weapon damage, preview-to-purchase consistency and existing player-owned items.",
        "",
        "## Authoritative architecture",
        "",
        "- `data/equipment_stat_policy.py` is the single source of class stat rules, allowed armor types, weapon subtypes, off-hand subtypes and weighted primary-stat choices.",
        "- `db_modules/generated_equipment.py` is the canonical calculation and generated-item creation owner.",
        "- `db_modules/shop.py` owns base-shop preview and purchase integration.",
        "- `systems/dynamic_equipment_system.py` is a thin lazy compatibility delegate with no SQL, balance tables, independent RNG logic or item creation.",
        "",
        "## Class profiles",
        "",
        "- Warrior: STR 60%, STA 30%, DEX 10%.",
        "- Knight: STA 50%, STR 45%, DEX 5%.",
        "- Scout: STR 45%, DEX 45%, STA 10%.",
        "- Rogue: DEX 60%, STR 30%, STA 10%.",
        "- Mage: INT 65%, WIS 25%, STA 10%.",
        "- Priest: INT 50%, WIS 40%, STA 10%.",
        "",
        "These percentages are weighted stat-selection probabilities. They are not PATK/MATK coefficients and do not increase the total generated stat budget.",
        "",
        "## Equipment rules",
        "",
        "- Mage and Priest use cloth.",
        "- Scout and Rogue use leather.",
        "- Warrior uses chain.",
        "- Knight uses plate.",
        "- Knight shield generates only STA and STR, weighted 65% and 35% for shield-specific selection.",
        "- Warrior and Knight swords may receive rare DEX as a secondary class stat.",
        "- Scout keeps both bow and crossbow subtypes.",
        "- Jewelry is class-aware: physical classes use STR/DEX/STA profiles; magical classes use INT/WIS/STA profiles.",
        "",
        "## Armor defense identity",
        "",
        "The existing armor defense distribution remains unchanged:",
        "",
        "- Cloth emphasizes MDEF.",
        "- Leather remains comparatively balanced.",
        "- Chain emphasizes PDEF.",
        "- Plate has the strongest PDEF emphasis.",
        "",
        "Class-aware primary-stat redistribution does not alter the already calculated PDEF/MDEF values.",
        "",
        "## Generation and shop flow",
        "",
        "- Class-aware mob loot applies the target character class only when the class-aware branch is selected.",
        "- Forced-slot generation and new base-shop previews always use the target user's class.",
        "- Preview creation generates the item once.",
        "- Purchase promotes the preview to a permanent generated item and does not reroll stats.",
        "- Existing generated and historical preview items are not migrated or recalculated.",
        "",
        "## Legacy route consolidation",
        "",
        "The broken legacy class-shop route no longer imports the missing `generate_equipment_item` symbol and no longer inserts a full parallel random shop into `items`. Its public functions remain available as read-only canonical offer descriptors.",
        "",
        "## Verification",
        "",
        "- Seven maintained Stage 18.17 tests PASS.",
        "- Drop/shop parity: 58 routes and 11,600 deterministic samples PASS.",
        "- Dynamic-equipment behavioral parity: 1,950 fixtures PASS.",
        "- Seventeen compatibility helpers preserve their signatures and delegate to the canonical owner.",
        "- `py_compile`, imports, structural contracts, exception contracts and RNG seed behavior PASS.",
        "- `PRAGMA quick_check`: ok.",
        "- Foreign-key violations: 0.",
        "- `game.db` remained unchanged during closure.",
        "- WAL/SHM were not manipulated.",
        "",
        "## Manual acceptance",
        "",
        "Manual verification was completed successfully after Stage 18.17.8. The base shop, class-appropriate stats, preview and purchase consistency, inventory, comparison, equip flow, PvE and restart were accepted without runtime traceback.",
        "",
        "## Known nuances",
        "",
    ]
    for nuance in report["known_nuances"]:
        lines.append(f"- {nuance}")
    lines.extend([
        "",
        "## Superseded point-in-time audits",
        "",
        "Stages 18.17.0, 18.17.4 and 18.17.5 remain historical evidence. Their pre-mutation findings are intentionally superseded by the current production invariants and are not treated as present defects.",
        "",
        "## Final decision",
        "",
        "Stage 18.17 is closed. No additional implementation patch is required unless a new runtime defect is discovered. Continue with Stage 18.18 according to the current roadmap.",
    ])
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "CLOSED",
        "maintained_tests": len(MAINTAINED_TESTS),
        "drop_shop_samples": 11600,
        "behavioral_fixtures": 1950,
        "manual_acceptance": "PASS",
        "db_unchanged": True,
        "json": str(REPORT.relative_to(ROOT)),
        "md": str(MD.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
