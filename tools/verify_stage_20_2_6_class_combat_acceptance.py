#!/usr/bin/env python3
"""Read-only verifier for Stage 20.2.6 class-combat acceptance."""
from __future__ import annotations
import ast
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSES = {
    "warrior": "physical", "knight": "physical",
    "scout": "physical", "rogue": "physical",
    "mage": "magical", "priest": "magical",
}
MAINTAINED = [
    "tools/verify_stage_20_2_2_class_basic_attack.py",
    "tools/verify_stage_20_2_2a_magical_basic_attack_stat_routing.py",
    "tools/verify_stage_20_2_3_pvp_simulator_basic_attack_parity.py",
    "tools/smoke_test_priest_healing_three_heals.py",
    "tools/smoke_test_priest_cooldown_display_20_2_5b.py",
]
EVIDENCE = [
    "reports/stage_20_2_2_class_basic_attack_type.json",
    "reports/stage_20_2_2a_magical_basic_attack_stat_routing.json",
    "reports/stage_20_2_3_pvp_simulator_basic_attack_parity.json",
    "reports/stage_20_2_5a_priest_three_heals.json",
    "reports/stage_20_2_5b_priest_description_and_cooldown.json",
]


def execute(relative):
    path = ROOT / relative
    if not path.is_file():
        return {"path": relative, "status": "MISSING"}
    process = subprocess.run(
        [sys.executable, relative], cwd=ROOT, text=True,
        capture_output=True, encoding="utf-8", errors="replace",
    )
    return {
        "path": relative,
        "status": "PASS" if process.returncode == 0 else "FAIL",
        "returncode": process.returncode,
        "stdout": process.stdout.strip()[-4000:],
        "stderr": process.stderr.strip()[-4000:],
    }


def read_json(relative):
    path = ROOT / relative
    if not path.is_file():
        return {"path": relative, "status": "MISSING"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return {
            "path": relative,
            "status": "PASS" if str(payload.get("status", "")).upper() == "PASS" else "PRESENT",
            "reported_status": payload.get("status"),
            "commit": payload.get("commit") or (payload.get("git_commit") or {}).get("hash"),
        }
    except Exception as exc:
        return {"path": relative, "status": "FAIL", "error": str(exc)}


def main():
    checks = []
    stat_path = ROOT / "systems" / "stat_system.py"
    stat_source = stat_path.read_text(encoding="utf-8-sig")
    ast.parse(stat_source)
    sys.path.insert(0, str(ROOT))
    from systems.stat_system import resolve_basic_attack_type
    actual = {key: resolve_basic_attack_type(key) for key in CLASSES}
    checks.append({"name": "six_class_basic_attack_matrix", "status": "PASS" if actual == CLASSES else "FAIL", "actual": actual})

    from data.priest_healing_policy import (
        PRIEST_HEALING_COOLDOWN_TURNS,
        PRIEST_HEALING_DURATION_TURNS,
        PRIEST_HEALING_IMMEDIATE_HEALS,
        PRIEST_HEALING_TOTAL_HEALS,
        build_priest_healing_effect,
        calculate_priest_heal_amount,
    )
    priest_ok = (
        PRIEST_HEALING_IMMEDIATE_HEALS == 1
        and PRIEST_HEALING_DURATION_TURNS == 2
        and PRIEST_HEALING_TOTAL_HEALS == 3
        and PRIEST_HEALING_COOLDOWN_TURNS == 4
        and build_priest_healing_effect(calculate_priest_heal_amount(130))["turns"] == 2
    )
    checks.append({"name": "priest_healing_contract", "status": "PASS" if priest_ok else "FAIL"})

    combat = (ROOT / "handlers" / "combat.py").read_text(encoding="utf-8-sig")
    cooldown_ok = (
        'mob["skill_cooldowns"][skill_key] = cooldown_turns + 1' not in combat
        and 'mob["skill_cooldowns"][skill_key] = cooldown_turns' in combat
    )
    checks.append({
        "name": "priest_visible_cooldown_regression",
        "status": "PASS" if cooldown_ok else "FAIL",
    })

    maintained = [execute(path) for path in MAINTAINED]
    evidence = [read_json(path) for path in EVIDENCE]
    available_maintained = [item for item in maintained if item["status"] != "MISSING"]
    maintained_ok = bool(available_maintained) and all(item["status"] == "PASS" for item in available_maintained)
    checks.append({"name": "maintained_suite", "status": "PASS" if maintained_ok else "FAIL", "available": len(available_maintained)})
    parity_path = "tools/verify_stage_20_2_3_pvp_simulator_basic_attack_parity.py"
    parity_result = next((item for item in maintained if item["path"] == parity_path), None)
    parity_ok = parity_result is not None and parity_result.get("status") == "PASS"
    checks.append({
        "name": "pvp_simulator_runtime_parity",
        "status": "PASS" if parity_ok else "FAIL",
        "authority": parity_path,
    })

    db_result = {"present": False, "status": "NOT_APPLICABLE"}
    db_path = ROOT / "game.db"
    if db_path.is_file():
        uri = db_path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        try:
            quick = [row[0] for row in connection.execute("PRAGMA quick_check")]
            foreign = list(connection.execute("PRAGMA foreign_key_check"))
            db_result = {
                "present": True, "mode": "ro", "quick_check": quick,
                "foreign_key_errors": len(foreign),
                "status": "PASS" if quick == ["ok"] and not foreign else "FAIL",
            }
        finally:
            connection.close()
    checks.append({"name": "database_invariants", "status": db_result["status"]})

    automated_pass = all(item["status"] in {"PASS", "NOT_APPLICABLE"} for item in checks)
    payload = {
        "stage": "20.2.6",
        "automated_status": "PASS" if automated_pass else "FAIL",
        "acceptance_status": "MANUAL_EVIDENCE_REQUIRED" if automated_pass else "BLOCKED_AUTOMATED_FAIL",
        "checks": checks,
        "maintained_suite": maintained,
        "prior_evidence": evidence,
        "database": db_result,
        "manual_gate": {
            "required": True,
            "scenarios": [
                "Mage basic attack PvE",
                "Priest basic attack and healing PvE",
                "One physical class basic attack PvE",
                "One magical and one physical class PvP",
                "Simulator sanity for all six classes",
            ],
        },
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if automated_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
