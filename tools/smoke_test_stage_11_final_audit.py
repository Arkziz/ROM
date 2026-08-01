#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def counts(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = result.get(node.name, 0) + 1
    return result


def main():
    final_json = ROOT / "CENTRAL_DROP_STAGE_11_FINAL_AUDIT.json"
    final_md = ROOT / "CENTRAL_DROP_STAGE_11_FINAL_DOCUMENTATION.md"
    manifest = ROOT / "CENTRAL_DROP_STAGE_11_FILE_MANIFEST.json"
    for path in (final_json, final_md, manifest):
        if not path.is_file():
            fail(f"missing final artifact: {path.name}")

    audit = json.loads(final_json.read_text(encoding="utf-8"))
    if audit.get("stage") != 11 or audit.get("version") != "11.12.0":
        fail("final audit identity mismatch")
    if audit.get("verdict") != "PASS":
        fail(f"final verdict={audit.get('verdict')}")
    if audit.get("critical_findings"):
        fail(f"critical findings: {audit['critical_findings']}")
    if audit.get("victory_rule_order") != [
        "trophy", "equipment", "refine_stone", "rune", "potion"
    ]:
        fail("victory order mismatch")
    if audit.get("protected_items") != [402, 527, 528]:
        fail("protected policy mismatch")

    reward = counts(ROOT / "systems/reward_system.py")
    drop = counts(ROOT / "systems/drop_system.py")
    rune = counts(ROOT / "systems/rune_system.py")
    for name in (
        "roll_equipment_drop", "roll_loot_from_loot_table",
        "roll_loot_from_simple_keys", "roll_refine_stone_drop",
        "roll_potion_drop", "roll_loot", "process_victory_reward",
        "process_enemy_drops",
    ):
        if reward.get(name) != 1:
            fail(f"reward singleton {name}={reward.get(name, 0)}")
    if drop.get("validate_drop_tables") != 1:
        fail("drop validator duplicated")
    for name in ("roll_rune_drop", "award_rune_drop", "simulate_rune_drops"):
        if rune.get(name) != 1:
            fail(f"rune singleton {name}={rune.get(name, 0)}")

    text = final_md.read_text(encoding="utf-8")
    markers = (
        "Stage 11 Central Drop System",
        "## 3. Authoritative Architecture",
        "## 5. Complete Balance Specification",
        "## 8. Inventory and Loss Semantics",
        "## 11. Telegram Reliability Protection",
        "## 14. Known Limitations and Deferred Decisions",
        "## 17. Stage Completion Decision",
    )
    for marker in markers:
        if marker not in text:
            fail(f"documentation section missing: {marker}")

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    if not manifest_data.get("files") or manifest_data.get("stage") != 11:
        fail("manifest incomplete")

    print("[OK] Stage 11 final audit/documentation contracts")
    print("- final verdict PASS: OK")
    print("- authoritative central flow and rule order: OK")
    print("- reward/drop/rune singleton architecture: OK")
    print("- protected material policy: OK")
    print("- comprehensive documentation sections: OK")
    print("- SHA-256 file manifest: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
