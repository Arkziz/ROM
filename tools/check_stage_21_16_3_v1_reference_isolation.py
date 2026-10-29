#!/usr/bin/env python3
"""Maintained verifier for Stage 21.16.3 V1 reference isolation evidence."""
from __future__ import annotations
import ast
import json
from pathlib import Path

REPORT = "reports/stage_21_16_3_v1_reference_isolation_audit.json"
FORBIDDEN = {"handlers", "systems", "db_modules", "keyboards", "events", "legacy"}

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / REPORT).read_text(encoding="utf-8-sig"))
    assert data["stage"] == "21.16.3" and data["status"] == "PASS"
    assert data["audit_mode"] == "READ_ONLY"
    assert data["summary"]["runtime_blocker_count"] == 0
    assert data["production_mutation"] is False
    assert data["database_opened"] is False
    assert data["v1_wal_shm_manipulated"] is False
    for path in sorted((root / "rom_v2").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name.split(".", 1)[0] not in FORBIDDEN for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in FORBIDDEN
    print("[PASS] Stage 21.16.3 V1 reference isolation audit evidence verified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
