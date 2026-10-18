"""Verify the complete ROM V2 schema contract without opening SQLite."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rom_v2.infrastructure.persistence.schema_contract import SCHEMA_CONTRACT

ALLOWED_TYPES = {"INTEGER", "REAL", "TEXT", "BLOB"}
ALLOWED_ACTIONS = {"CASCADE", "RESTRICT", "SET NULL", "NO ACTION"}
REQUIRED_TABLES = {"accounts", "characters", "character_primary_stats", "gold_wallets", "crystal_wallets", "crystal_ledger", "item_instances", "equipment_slots", "item_reservations", "quest_progress", "quest_item_balances", "operation_records", "domain_events", "outbox_messages", "schema_migrations"}
REQUIRED_DEFERRED = {"travel", "guild", "direct_trade", "auction", "pvp_history", "premium", "daily_rewards", "notifications", "ratings_chronicles", "events", "runes_sockets"}

def verify_contract() -> dict[str, Any]:
    """Return complete deterministic findings for the schema contract."""
    tables = dict(SCHEMA_CONTRACT["tables"])
    violations: list[dict[str, str]] = []
    if set(tables) != REQUIRED_TABLES:
        violations.append({"rule": "TABLE_SET", "detail": str(sorted(set(tables) ^ REQUIRED_TABLES))})
    for table_name, raw in sorted(tables.items()):
        table = dict(raw); columns = dict(table.get("columns", {})); primary_key = list(table.get("primary_key", []))
        if not table.get("owner"): violations.append({"rule": "MISSING_OWNER", "detail": table_name})
        if not primary_key or not set(primary_key).issubset(columns): violations.append({"rule": "PRIMARY_KEY", "detail": table_name})
        for column_name, raw_column in columns.items():
            spec = dict(raw_column)
            if spec.get("storage_type") not in ALLOWED_TYPES: violations.append({"rule": "COLUMN_TYPE", "detail": f"{table_name}.{column_name}"})
            if not isinstance(spec.get("nullable"), bool): violations.append({"rule": "NULLABILITY", "detail": f"{table_name}.{column_name}"})
            if not spec.get("generated_by"): violations.append({"rule": "GENERATION_OWNER", "detail": f"{table_name}.{column_name}"})
            if column_name in primary_key and spec.get("nullable"): violations.append({"rule": "NULLABLE_PRIMARY_KEY", "detail": f"{table_name}.{column_name}"})
        for unique in table.get("unique", []):
            if not unique or not set(unique).issubset(columns): violations.append({"rule": "UNIQUE_COLUMNS", "detail": f"{table_name}:{unique}"})
        for fk in table.get("foreign_keys", []):
            column_name=fk.get("column"); target=fk.get("target_table"); target_column=fk.get("target_column")
            if column_name not in columns or target not in tables or target_column not in dict(tables.get(target, {})).get("columns", {}): violations.append({"rule": "FOREIGN_KEY_TARGET", "detail": f"{table_name}:{fk}"})
            if fk.get("on_delete") not in ALLOWED_ACTIONS or fk.get("on_update") not in ALLOWED_ACTIONS: violations.append({"rule": "FOREIGN_KEY_ACTION", "detail": f"{table_name}:{fk}"})
    names: set[str] = set()
    for index in SCHEMA_CONTRACT["indexes"]:
        name=index.get("name"); table=index.get("table"); columns=index.get("columns", [])
        if not name or name in names: violations.append({"rule": "INDEX_NAME", "detail": str(name)})
        names.add(str(name))
        if table not in tables or not columns or not set(columns).issubset(dict(tables.get(table, {})).get("columns", {})): violations.append({"rule": "INDEX_COLUMNS", "detail": str(index)})
    deferred = dict(SCHEMA_CONTRACT.get("deferred_domains", {}))
    if set(deferred) != REQUIRED_DEFERRED: violations.append({"rule": "DEFERRED_DOMAIN_SET", "detail": str(sorted(set(deferred) ^ REQUIRED_DEFERRED))})
    for name, decision in deferred.items():
        if decision.get("decision") != "deferred_no_placeholder_table" or not decision.get("future_owner"): violations.append({"rule": "DEFERRED_DOMAIN_DECISION", "detail": name})
    if SCHEMA_CONTRACT.get("development_strategy") != "clean_reset_first": violations.append({"rule": "RESET_STRATEGY", "detail": "clean reset required"})
    if SCHEMA_CONTRACT.get("v1_data_strategy") != "do_not_migrate_test_data": violations.append({"rule": "V1_DATA_STRATEGY", "detail": "V1 test data must not migrate"})
    if SCHEMA_CONTRACT.get("money_policy") != "integer_minor_units": violations.append({"rule": "MONEY_POLICY", "detail": "integer minor units required"})
    if SCHEMA_CONTRACT.get("timestamp_policy") != "utc_iso8601_text": violations.append({"rule": "TIMESTAMP_POLICY", "detail": "UTC ISO-8601 required"})
    return {"status": "PASS" if not violations else "FAIL", "contract_revision": SCHEMA_CONTRACT["contract_revision"], "table_count": len(tables), "column_count": sum(len(dict(t["columns"])) for t in tables.values()), "index_count": len(SCHEMA_CONTRACT["indexes"]), "deferred_domain_count": len(deferred), "tables": tables, "indexes": list(SCHEMA_CONTRACT["indexes"]), "deferred_domains": deferred, "violations": violations}

def main() -> int:
    """Run verification and optionally persist full JSON evidence."""
    parser=argparse.ArgumentParser(); parser.add_argument("--project-root", default="."); parser.add_argument("--json-out"); args=parser.parse_args(); result=verify_contract()
    if args.json_out:
        path=Path(args.json_out); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"V2 schema contract: {result['status']}"); print(f"Revision: {result['contract_revision']}"); print(f"Tables: {result['table_count']}"); print(f"Columns: {result['column_count']}"); print(f"Indexes: {result['index_count']}"); print(f"Deferred domains: {result['deferred_domain_count']}"); print(f"Violations: {len(result['violations'])}")
    return 0 if result["status"] == "PASS" else 1
if __name__ == "__main__": raise SystemExit(main())
