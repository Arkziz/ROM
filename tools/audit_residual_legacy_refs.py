#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i4e: verify residual legacy references are fully cleaned."""
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db.py"
READINESS_PATH = ROOT / "tools" / "db_cleanup_readiness.py"
REPORT_PATH = ROOT / "DB_CLEANUP_9_0_12I4E_RESIDUAL_LEGACY_REFS_CLEANUP.md"
EXPECTED_PATTERN = r"(?<![A-Za-z0-9_])_legacy_[A-Za-z0-9_]+"
REMOVED_CAPTURE = "_legacy_process_passive_regeneration_before_hp_dynamic_max_fix_v1"
PRESERVED_MIGRATION = "migrate_legacy_equipment_to_slots"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    db_text = DB_PATH.read_text(encoding="utf-8-sig")
    readiness_text = READINESS_PATH.read_text(encoding="utf-8-sig")
    tree = ast.parse(db_text, filename=str(DB_PATH))

    if REMOVED_CAPTURE in db_text:
        fail("unused regen capture is still present")
    if PRESERVED_MIGRATION not in db_text:
        fail("migrate_legacy_equipment_to_slots was removed or renamed")
    if EXPECTED_PATTERN not in readiness_text:
        fail("readiness regex was not updated to the identifier-boundary pattern")

    matches = sorted(set(re.compile(EXPECTED_PATTERN).findall(db_text)))
    if matches:
        fail(f"real legacy identifiers remain: {matches}")

    regen_defs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "process_passive_regeneration"
    ]
    if not regen_defs:
        fail("process_passive_regeneration is missing")
    final_regen = ast.get_source_segment(db_text, regen_defs[-1]) or ""
    if "regen_system" not in final_regen:
        fail("final process_passive_regeneration does not delegate to regen_system")

    migration_defs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == PRESERVED_MIGRATION
    ]
    if len(migration_defs) != 1:
        fail(f"{PRESERVED_MIGRATION} definitions={len(migration_defs)}, expected 1")

    report = [
        "# ROM 9.0.12i4e - Residual Legacy References Cleanup",
        "",
        "## Result",
        "",
        "- Unused regen compatibility capture removed: yes",
        "- Readiness regex identifier boundary fixed: yes",
        "- `migrate_legacy_equipment_to_slots` preserved: yes",
        "- Real `_legacy_*` identifiers remaining in `db.py`: 0",
        "- Final `process_passive_regeneration` delegates to `systems.regen_system`: yes",
        "- Database mutations performed by this verification: 0",
        "",
        "## Expected readiness",
        "",
        "- `legacy_refs`: 0",
        "- `unsafe_delete`: 0",
        "",
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    print("[OK] residual legacy refs post-cleanup")
    print("- real legacy identifiers: 0")
    print("- unused regen capture: removed")
    print("- readiness regex boundary: fixed")
    print("- migrate_legacy_equipment_to_slots preserved: yes")
    print("- regen system delegation: OK")
    print("- database mutations: 0")
    print(f"- report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
