"""Verify the ROM V2 domain-oriented schema contract without opening SQLite."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

# Direct execution sets sys.path[0] to tools/. Add the project root explicitly
# so the verifier imports the physical rom_v2 package identically in local CI.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT

REQUIRED_TABLES = {"accounts", "characters", "character_primary_stats", "gold_wallets", "crystal_wallets", "crystal_ledger", "item_instances", "equipment_slots", "item_reservations", "quest_progress", "quest_item_balances", "operation_records", "domain_events", "outbox_messages", "schema_migrations"}
REQUIRED_FORBIDDEN = {"v1_migration_chain_copy", "sql_in_domain", "sql_in_handlers", "float_money", "localized_technical_keys", "critical_state_only_in_memory"}

def verify_contract() -> dict[str, Any]:
    """Return complete deterministic schema findings."""
    tables = dict(SCHEMA_CONTRACT["tables"])
    violations: list[dict[str, str]] = []
    missing = sorted(REQUIRED_TABLES - set(tables))
    if missing: violations.append({"rule": "REQUIRED_TABLES", "detail": ",".join(missing)})
    for name, raw in sorted(tables.items()):
        table = dict(raw)
        if not table.get("owner"): violations.append({"rule": "MISSING_OWNER", "detail": name})
        pk = list(table.get("primary_key", [])); columns = set(table.get("columns", []))
        if not pk or not set(pk).issubset(columns): violations.append({"rule": "INVALID_PRIMARY_KEY", "detail": name})
        for fk in table.get("foreign_keys", []):
            if len(fk) != 3 or fk[0] not in columns or fk[1] not in tables:
                violations.append({"rule": "INVALID_FOREIGN_KEY", "detail": f"{name}:{fk}"})
        for unique in table.get("unique", []):
            if not set(unique).issubset(columns): violations.append({"rule": "INVALID_UNIQUE", "detail": f"{name}:{unique}"})
    if SCHEMA_CONTRACT.get("money_policy") != "integer_minor_units": violations.append({"rule": "MONEY_POLICY", "detail": "integer minor units required"})
    if SCHEMA_CONTRACT.get("timestamp_policy") != "utc_iso8601_text": violations.append({"rule": "UTC_POLICY", "detail": "UTC ISO-8601 required"})
    if not SCHEMA_CONTRACT.get("foreign_keys_required"): violations.append({"rule": "FOREIGN_KEYS", "detail": "foreign keys required"})
    if set(SCHEMA_CONTRACT.get("forbidden_designs", [])) != REQUIRED_FORBIDDEN: violations.append({"rule": "FORBIDDEN_DESIGNS", "detail": "contract mismatch"})
    return {"status": "PASS" if not violations else "FAIL", "table_count": len(tables), "index_count": len(SCHEMA_CONTRACT["indexes"]), "tables": tables, "indexes": list(SCHEMA_CONTRACT["indexes"]), "violations": violations}

def main() -> int:
    """Run verification and optionally persist JSON evidence."""
    parser=argparse.ArgumentParser(); parser.add_argument("--project-root", default="."); parser.add_argument("--json-out")
    args=parser.parse_args(); result=verify_contract()
    if args.json_out:
        path=Path(args.json_out); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"V2 schema contract: {result['status']}"); print(f"Tables: {result['table_count']}"); print(f"Indexes: {result['index_count']}"); print(f"Violations: {len(result['violations'])}")
    return 0 if result["status"] == "PASS" else 1
if __name__ == "__main__": raise SystemExit(main())
