#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_5_existing_about_links_support_audit.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.5"
assert data["status"] == "PASS"
assert data["summary"]["next_action"] == "GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW"
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.14.5 existing About/links/support audit")
