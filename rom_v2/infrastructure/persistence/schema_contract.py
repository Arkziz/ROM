"""Machine-readable domain-oriented SQLite schema contract for ROM V2."""
from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

# This contract describes ownership and invariants only. Stage 21.5.2 owns SQL DDL.
_SCHEMA: Final[dict[str, object]] = {
    "schema_version": 1,
    "database_engine": "sqlite",
    "timestamp_policy": "utc_iso8601_text",
    "money_policy": "integer_minor_units",
    "foreign_keys_required": True,
    "tables": {
        "accounts": {"owner": "account", "primary_key": ["account_id"], "columns": ["account_id", "telegram_user_id", "status", "registered_at_utc", "bag_capacity", "version"], "unique": [["telegram_user_id"]]},
        "characters": {"owner": "character", "primary_key": ["character_id"], "columns": ["character_id", "account_id", "name", "class_key", "level", "experience", "location_key", "current_hp", "current_mp", "version"], "foreign_keys": [["account_id", "accounts", "account_id"]], "unique": [["account_id"], ["name"]]},
        "character_primary_stats": {"owner": "stats", "primary_key": ["character_id"], "columns": ["character_id", "strength", "dexterity", "intelligence", "wisdom", "stamina", "unspent_points"], "foreign_keys": [["character_id", "characters", "character_id"]]},
        "gold_wallets": {"owner": "economy", "primary_key": ["character_id"], "columns": ["character_id", "balance_minor", "version"], "foreign_keys": [["character_id", "characters", "character_id"]]},
        "crystal_wallets": {"owner": "economy", "primary_key": ["account_id"], "columns": ["account_id", "balance", "version"], "foreign_keys": [["account_id", "accounts", "account_id"]]},
        "crystal_ledger": {"owner": "economy", "primary_key": ["entry_id"], "columns": ["entry_id", "account_id", "operation_id", "amount", "reason_key", "created_at_utc"], "foreign_keys": [["account_id", "accounts", "account_id"]], "unique": [["operation_id"]], "append_only": True},
        "item_instances": {"owner": "inventory", "primary_key": ["item_instance_id"], "columns": ["item_instance_id", "definition_key", "owner_character_id", "quantity", "durability", "enhancement_level", "binding_key", "version"], "foreign_keys": [["owner_character_id", "characters", "character_id"]]},
        "equipment_slots": {"owner": "equipment", "primary_key": ["character_id", "slot_key"], "columns": ["character_id", "slot_key", "item_instance_id"], "foreign_keys": [["character_id", "characters", "character_id"], ["item_instance_id", "item_instances", "item_instance_id"]], "unique": [["item_instance_id"]]},
        "item_reservations": {"owner": "inventory", "primary_key": ["reservation_id"], "columns": ["reservation_id", "item_instance_id", "operation_id", "purpose_key", "quantity", "expires_at_utc"], "foreign_keys": [["item_instance_id", "item_instances", "item_instance_id"]], "unique": [["operation_id", "item_instance_id"]]},
        "quest_progress": {"owner": "story", "primary_key": ["character_id", "quest_key"], "columns": ["character_id", "quest_key", "state_key", "progress_json", "completed_at_utc", "version"], "foreign_keys": [["character_id", "characters", "character_id"]]},
        "quest_item_balances": {"owner": "story", "primary_key": ["character_id", "item_key"], "columns": ["character_id", "item_key", "quantity"], "foreign_keys": [["character_id", "characters", "character_id"]]},
        "operation_records": {"owner": "application", "primary_key": ["operation_id"], "columns": ["operation_id", "operation_key", "aggregate_type", "aggregate_id", "status_key", "result_fingerprint", "created_at_utc", "completed_at_utc"], "unique": [["operation_id"]]},
        "domain_events": {"owner": "application", "primary_key": ["event_id"], "columns": ["event_id", "event_key", "aggregate_type", "aggregate_id", "aggregate_version", "sequence", "occurred_at_utc", "payload_json", "correlation_id", "causation_id", "schema_version"], "unique": [["aggregate_type", "aggregate_id", "aggregate_version", "sequence"]], "append_only": True},
        "outbox_messages": {"owner": "infrastructure", "primary_key": ["message_id"], "columns": ["message_id", "event_id", "topic_key", "payload_json", "created_at_utc", "published_at_utc", "attempt_count"], "foreign_keys": [["event_id", "domain_events", "event_id"]], "unique": [["event_id", "topic_key"]]},
        "schema_migrations": {"owner": "infrastructure", "primary_key": ["version"], "columns": ["version", "migration_key", "applied_at_utc", "checksum"], "unique": [["migration_key"]], "append_only": True},
    },
    "indexes": [
        ["characters", ["location_key"]], ["item_instances", ["owner_character_id", "definition_key"]],
        ["quest_progress", ["character_id", "state_key"]], ["domain_events", ["aggregate_type", "aggregate_id", "aggregate_version"]],
        ["outbox_messages", ["published_at_utc", "created_at_utc"]], ["operation_records", ["aggregate_type", "aggregate_id"]],
    ],
    "forbidden_designs": ["v1_migration_chain_copy", "sql_in_domain", "sql_in_handlers", "float_money", "localized_technical_keys", "critical_state_only_in_memory"],
}

SCHEMA_CONTRACT: Mapping[str, object] = MappingProxyType(_SCHEMA)
