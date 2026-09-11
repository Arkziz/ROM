#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic behavioral parity fixtures for dynamic-equipment helpers."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db_modules.generated_equipment as canonical
from systems import dynamic_equipment_system as compatibility

DB = ROOT / "game.db"
REPORT = ROOT / "reports/stage_18_17_7_dynamic_equipment_behavioral_fixtures.json"
MD = ROOT / "MD/STAGE_18_17_7_DYNAMIC_EQUIPMENT_BEHAVIORAL_FIXTURES.md"
TARGETS = (
    "add_primary_stat_to_stats",
    "apply_armor_type_defense_profile_to_stats",
    "apply_armor_type_primary_stat_profile_to_stats",
    "clear_primary_stat_bonuses",
    "get_existing_primary_stat_budget",
    "pick_weighted_stat",
)
PRIMARY_COLUMNS = ("bonus_str", "bonus_dex", "bonus_int", "bonus_wis", "bonus_sta")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def db_check():
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


def normalized(value):
    if isinstance(value, dict):
        return {key: normalized(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [normalized(item) for item in value]
    return value


def invoke(module, name, args, seed):
    working_args = copy.deepcopy(args)
    if seed is not None:
        random.seed(seed)
    try:
        value = getattr(module, name)(*working_args)
        outcome = {"kind": "return", "value": normalized(value)}
    except Exception as error:
        outcome = {"kind": "exception", "type": type(error).__name__, "message": str(error)}
    return outcome, normalized(working_args)


def compare_mutator(name, args, *, seed=None):
    left_outcome, left_args = invoke(canonical, name, args, seed)
    right_outcome, right_args = invoke(compatibility, name, args, seed)
    assert left_outcome == right_outcome, (name, seed, left_outcome, right_outcome)
    assert left_args == right_args, (name, seed, left_args, right_args)
    return {"name": name, "seed": seed, "outcome": left_outcome, "args_after": left_args}


def compare_pure(name, args, *, seed=None):
    left_outcome, left_args = invoke(canonical, name, args, seed)
    right_outcome, right_args = invoke(compatibility, name, args, seed)
    assert left_outcome == right_outcome, (name, seed, left_outcome, right_outcome)
    assert left_args == right_args, (name, seed, left_args, right_args)
    return {"name": name, "seed": seed, "outcome": left_outcome}


def main():
    for name in TARGETS:
        assert callable(getattr(canonical, name, None)), name
        assert callable(getattr(compatibility, name, None)), name

    results = []
    base_stats = [
        {},
        {"bonus_str": 0, "bonus_dex": 0, "bonus_int": 0, "bonus_wis": 0, "bonus_sta": 0},
        {"bonus_str": 7, "bonus_dex": 5, "bonus_int": 3, "bonus_wis": 2, "bonus_sta": 4},
        {"bonus_str": "6", "bonus_dex": None, "bonus_int": -2, "bonus_wis": 1.8, "bonus_sta": 0},
        {"pdef": 11, "mdef": 13, "bonus_sta": 4, "custom": "preserve"},
    ]

    complete_primary_stats = {
        "bonus_str": 2,
        "bonus_dex": 0,
        "bonus_int": 0,
        "bonus_wis": 0,
        "bonus_sta": 0,
        "custom": 9,
    }
    for stat_key in ("str", "dex", "int", "wis", "sta", "unknown"):
        for value in (0, 1, 5, -2, "3", None):
            results.append(compare_mutator("add_primary_stat_to_stats", (complete_primary_stats, stat_key, value)))

    # Invalid partial dictionaries are contract-edge fixtures. Matching exception
    # type/message and matching partial mutation count as behavioral parity.
    for stat_key in ("dex", "int", "wis", "sta"):
        results.append(compare_mutator("add_primary_stat_to_stats", ({"bonus_str": 2, "custom": 9}, stat_key, 1)))

    for stats in base_stats:
        results.append(compare_mutator("clear_primary_stat_bonuses", (stats,)))
        results.append(compare_pure("get_existing_primary_stat_budget", (stats,)))

    weighted_profiles = [
        (("str", 60), ("sta", 30), ("dex", 10)),
        (("int", 65), ("wis", 25), ("sta", 10)),
        (("sta", 65), ("str", 35)),
        (("dex", 100),),
        (),
    ]
    for profile in weighted_profiles:
        for excluded in (None, "str", "sta", "unknown"):
            for seed in range(25):
                results.append(compare_pure("pick_weighted_stat", (profile, excluded), seed=seed))

    armor_inputs = [
        {"pdef": 0, "mdef": 0},
        {"pdef": 1, "mdef": 1},
        {"pdef": 10, "mdef": 5, "bonus_str": 4, "bonus_dex": 3, "bonus_sta": 2},
        {"pdef": 3, "mdef": 17, "bonus_int": 8, "bonus_wis": 5, "custom": "keep"},
        {"pdef": "9", "mdef": None, "bonus_sta": "4"},
    ]
    for armor_type in ("cloth", "leather", "chain", "plate", "", None, "unknown"):
        for stats in armor_inputs:
            for seed in range(20):
                results.append(compare_mutator("apply_armor_type_primary_stat_profile_to_stats", (stats, armor_type), seed=seed))
                results.append(compare_mutator("apply_armor_type_defense_profile_to_stats", (stats, armor_type), seed=seed))

    # Explicit defense identity checks use canonical output after parity is proven.
    for armor_type in ("cloth", "leather", "chain", "plate"):
        random.seed(181707)
        output = canonical.apply_armor_type_defense_profile_to_stats(
            {"pdef": 12, "mdef": 8, "bonus_str": 4, "bonus_dex": 3, "bonus_int": 2, "bonus_wis": 1, "bonus_sta": 5},
            armor_type,
        )
        if armor_type == "cloth":
            assert output["mdef"] > output["pdef"]
        if armor_type == "plate":
            assert output["pdef"] > output["mdef"]

    db = db_check()
    assert db["quick_check"] == "ok"
    assert db["foreign_key_violations"] == []
    assert db["total_changes"] == 0
    assert db["unchanged"] is True

    counts = {}
    for name in TARGETS:
        counts[name] = sum(row["name"] == name for row in results)

    report = {
        "stage": "18.17.7",
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "production_mutation": False,
        "canonical_module": "db_modules.generated_equipment",
        "compatibility_module": "systems.dynamic_equipment_system",
        "functions": list(TARGETS),
        "fixture_counts": counts,
        "total_fixtures": len(results),
        "behavioral_parity": True,
        "database": db,
        "consolidation_decision": {
            "all_six_previously_non_equivalent_ast_functions_are_behaviorally_equivalent": True,
            "safe_to_prepare_thin_delegate_mutation": True,
            "preserve_signatures": True,
            "preserve_rng_seed_behavior": True,
            "next_patch": "18.17.8 dynamic equipment thin compatibility delegate",
        },
    }
    REPORT.parent.mkdir(exist_ok=True)
    MD.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Stage 18.17.7: Dynamic Equipment Behavioral Fixtures",
        "",
        "**Status:** PASS",
        "**Production mutation:** none",
        "",
        "## Behavioral parity",
        "",
        "The six same-signature but AST-different helper functions were compared deterministically between `db_modules.generated_equipment` and `systems.dynamic_equipment_system`.",
        "",
    ]
    for name in TARGETS:
        lines.append(f"- `{name}`: `{counts[name]}` fixtures PASS.")
    lines.extend([
        "",
        f"Total fixtures: **{len(results)}**.",
        "",
        "## Verified behavior",
        "",
        "- Return values, exception contracts and in-place argument mutations are equal.",
        "- Weighted RNG behavior is equal for identical seeds.",
        "- Unknown and empty armor profiles remain behaviorally equal.",
        "- Cloth and plate defense identities remain intact.",
        "- Custom dictionary fields remain preserved equally.",
        "",
        "## Consolidation decision",
        "",
        "The six previously blocked helpers are behaviorally equivalent and may be replaced by thin compatibility delegates while preserving their current signatures.",
        "",
        "## Database safety",
        "",
        f"- quick_check: `{db['quick_check']}`.",
        f"- FK violations: `{len(db['foreign_key_violations'])}`.",
        f"- DB unchanged: `{db['unchanged']}`.",
    ])
    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "PASS",
        "functions": len(TARGETS),
        "fixtures": len(results),
        "behavioral_parity": True,
        "db_unchanged": True,
        "json": str(REPORT.relative_to(ROOT)),
        "md": str(MD.relative_to(ROOT)),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
