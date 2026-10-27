#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_5b_about_links_support_parity_resolution.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.5b"
assert data["status"] == "PASS"
assert data["decision"] == "PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert not data["failed_checks"]
assert all(item["status"] == "RESOLVED" for item in data["resolutions"])
assert data["environment_file_opened"] is False
assert data["production_sqlite_opened"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
areas = {item["area"] for item in data["resolutions"]}
assert areas == {"about_content", "configuration", "url_validation", "useful_links_visibility", "support", "navigation", "runtime_boundary"}
print("PASS: Stage 21.14.5b About/links/support parity resolution")
