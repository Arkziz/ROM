#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_4b_ratings_history_chronicles_parity_resolution.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.4b"
assert data["status"] == "PASS"
assert data["decision"] == "PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert data["unresolved_after_resolution"] == []
assert {item["area"] for item in data["resolutions"]} == {'ratings_categories', 'persistence_and_runtime_boundary', 'ratings_own_position', 'profile_history_retention', 'ratings_ordering', 'ratings_top_and_page', 'chronicles_scope', 'chronicles_navigation', 'chronicles_ordering', 'profile_history_scope'}
assert all(item["status"] == "RESOLVED" for item in data["resolutions"])
assert data["ratings"]["top_limit"] == 100
assert data["ratings"]["page_size"] == 20
assert data["chronicles"]["retention_count"] == 100
assert data["chronicles"]["page_size"] == 10
assert data["profile_history"]["retention_count_per_type"] == 100
assert data["profile_history"]["minimum_retention_days"] == 60
print("PASS: Stage 21.14.4b ratings/history/chronicles parity resolution")
