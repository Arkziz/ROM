"""Validate Stage 21.16.3 read-only isolation-audit artifact."""
from __future__ import annotations
import json,sys
from pathlib import Path
def main():
 root=Path(__file__).resolve().parent.parent
 p=root/"reports/stage_21_16_3_v1_reference_isolation_audit.json"
 d=json.loads(p.read_text(encoding="utf-8-sig"))
 assert d["stage"]=="21.16.3" and d["status"]=="PASS"
 assert d["audit_mode"]=="READ_ONLY" and d["production_mutation"] is False
 assert d["database_opened"] is False and d["v1_wal_shm_manipulated"] is False
 assert d["next_stage"]=="21.16.3a"
 assert isinstance(d["findings"],list) and "runtime_blocker_count" in d["summary"]
 print("PASS: Stage 21.16.3 isolation audit artifact validated")
 return 0
if __name__=="__main__":raise SystemExit(main())
