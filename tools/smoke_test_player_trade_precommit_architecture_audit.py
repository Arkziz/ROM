#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
J=ROOT/"PLAYER_TRADE_12_6_7_PRECOMMIT_ARCHITECTURE_AUDIT.json"; M=ROOT/"PLAYER_TRADE_12_6_7_PRECOMMIT_ARCHITECTURE_AUDIT.md"
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)
def main():
    if not J.exists() or not M.exists(): fail("audit artifacts missing")
    d=json.loads(J.read_text(encoding="utf-8"))
    if d.get("stage")!="12.6.7" or d.get("mode")!="read_only": fail("stage/mode mismatch")
    if d.get("gameplay_mutations")!=0 or d.get("database_writes")!=0: fail("mutations reported")
    if d.get("verdict") not in {"PASS","REVIEW"} or not d.get("ready_for_12_7"): fail("audit not ready")
    for k in ("handler_level_guard","no_dispatcher_wrapper","status_noop","inline_refresh","manual_amount_input","trade_domain_api","trade_schema","ready_confirm_columns","database_integrity","no_orphan_state"):
        if d.get("readiness",{}).get(k) is not True: fail(f"readiness failed: {k}")
    h=d["source"]["handlers/player_interaction.py"]
    if h.get("process_new_updates_assignments") or h.get("dispatcher_lock_count")!=0 or h.get("handler_level_guard_count")!=1: fail("navigation architecture mismatch")
    db=d["database"]
    if db.get("quick_check")!="ok" or db.get("foreign_key_issue_count")!=0 or any(db.get("orphan_counts",{}).values()): fail("database state mismatch")
    md=M.read_text(encoding="utf-8")
    if "BEGIN IMMEDIATE" not in md or "Обов'язковий план для 12.7.0" not in md: fail("documentation incomplete")
    print("[OK] Player trade pre-commit audit contracts")
    print("- handler-level navigation architecture: OK")
    print("- trade schema and ready/confirm columns: OK")
    print("- reservations and activity state are clean: OK")
    print("- database integrity: OK")
    print("- ready for Stage 12.7: OK")
    print("- gameplay mutations: 0")
    print("- database writes: 0")
if __name__=="__main__": main()
