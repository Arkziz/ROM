"""Complete machine-readable SQLite schema contract for ROM V2."""
from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping


def column(
    storage_type: str,
    *,
    nullable: bool = False,
    default: str | int | None = None,
    generated_by: str = "application",
    checks: tuple[str, ...] = (),
) -> dict[str, object]:
    """Build an immutable-by-convention column specification."""
    return {
        "storage_type": storage_type,
        "nullable": nullable,
        "default": default,
        "generated_by": generated_by,
        "checks": list(checks),
    }


def foreign_key(
    column_name: str,
    target_table: str,
    target_column: str,
    *,
    on_delete: str,
    on_update: str = "CASCADE",
) -> dict[str, str]:
    """Build one explicit foreign-key action contract."""
    return {
        "column": column_name,
        "target_table": target_table,
        "target_column": target_column,
        "on_delete": on_delete,
        "on_update": on_update,
    }


_SCHEMA: Final[dict[str, object]] = {
    "contract_revision": "21.5.1b",
    "schema_version": 1,
    "database_engine": "sqlite",
    "development_strategy": "clean_reset_first",
    "v1_data_strategy": "do_not_migrate_test_data",
    "timestamp_policy": "utc_iso8601_text",
    "money_policy": "integer_minor_units",
    "foreign_keys_required": True,
    "journal_mode_managed_by_connection_factory": True,
    "tables": {
        "accounts": {
            "owner": "account",
            "primary_key": ["account_id"],
            "columns": {
                "account_id": column("TEXT", generated_by="application_uuid"),
                "telegram_user_id": column("INTEGER", checks=("telegram_user_id > 0",)),
                "status": column("TEXT", default="active", checks=("status IN ('active','blocked','closed')",)),
                "registered_at_utc": column("TEXT"),
                "bag_capacity": column("INTEGER", default=60, checks=("bag_capacity BETWEEN 1 AND 1000",)),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "unique": [["telegram_user_id"]],
            "checks": ["length(account_id) > 0", "length(registered_at_utc) > 0"],
        },
        "characters": {
            "owner": "character",
            "primary_key": ["character_id"],
            "columns": {
                "character_id": column("TEXT", generated_by="application_uuid"),
                "account_id": column("TEXT"),
                "name": column("TEXT", checks=("length(trim(name)) BETWEEN 1 AND 64",)),
                "class_key": column("TEXT", checks=("length(class_key) > 0",)),
                "level": column("INTEGER", default=1, checks=("level >= 1",)),
                "experience": column("INTEGER", default=0, checks=("experience >= 0",)),
                "location_key": column("TEXT", checks=("length(location_key) > 0",)),
                "current_hp": column("INTEGER", checks=("current_hp >= 0",)),
                "current_mp": column("INTEGER", nullable=True, checks=("current_mp IS NULL OR current_mp >= 0",)),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "foreign_keys": [foreign_key("account_id", "accounts", "account_id", on_delete="CASCADE")],
            "unique": [["account_id"], ["name"]],
            "checks": ["length(character_id) > 0"],
        },
        "character_primary_stats": {
            "owner": "stats",
            "primary_key": ["character_id"],
            "columns": {
                "character_id": column("TEXT"),
                "strength": column("INTEGER", checks=("strength >= 0",)),
                "dexterity": column("INTEGER", checks=("dexterity >= 0",)),
                "intelligence": column("INTEGER", checks=("intelligence >= 0",)),
                "wisdom": column("INTEGER", checks=("wisdom >= 0",)),
                "stamina": column("INTEGER", checks=("stamina >= 0",)),
                "unspent_points": column("INTEGER", default=0, checks=("unspent_points >= 0",)),
            },
            "foreign_keys": [foreign_key("character_id", "characters", "character_id", on_delete="CASCADE")],
        },
        "gold_wallets": {
            "owner": "economy",
            "primary_key": ["character_id"],
            "columns": {
                "character_id": column("TEXT"),
                "balance_minor": column("INTEGER", default=0, checks=("balance_minor >= 0",)),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "foreign_keys": [foreign_key("character_id", "characters", "character_id", on_delete="CASCADE")],
        },
        "crystal_wallets": {
            "owner": "economy",
            "primary_key": ["account_id"],
            "columns": {
                "account_id": column("TEXT"),
                "balance": column("INTEGER", default=0, checks=("balance >= 0",)),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "foreign_keys": [foreign_key("account_id", "accounts", "account_id", on_delete="CASCADE")],
        },
        "crystal_ledger": {
            "owner": "economy",
            "primary_key": ["entry_id"],
            "columns": {
                "entry_id": column("TEXT", generated_by="application_uuid"),
                "account_id": column("TEXT"),
                "operation_id": column("TEXT"),
                "amount": column("INTEGER", checks=("amount <> 0",)),
                "reason_key": column("TEXT", checks=("length(reason_key) > 0",)),
                "created_at_utc": column("TEXT"),
            },
            "foreign_keys": [
                foreign_key("account_id", "accounts", "account_id", on_delete="RESTRICT"),
                foreign_key("operation_id", "operation_records", "operation_id", on_delete="RESTRICT"),
            ],
            "unique": [["operation_id"]],
            "append_only": True,
        },
        "item_instances": {
            "owner": "inventory",
            "primary_key": ["item_instance_id"],
            "columns": {
                "item_instance_id": column("TEXT", generated_by="application_uuid"),
                "definition_key": column("TEXT", checks=("length(definition_key) > 0",)),
                "owner_character_id": column("TEXT"),
                "quantity": column("INTEGER", default=1, checks=("quantity > 0",)),
                "durability": column("INTEGER", nullable=True, checks=("durability IS NULL OR durability BETWEEN 0 AND 100",)),
                "enhancement_level": column("INTEGER", default=0, checks=("enhancement_level >= 0",)),
                "binding_key": column("TEXT", default="unbound", checks=("length(binding_key) > 0",)),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "foreign_keys": [foreign_key("owner_character_id", "characters", "character_id", on_delete="CASCADE")],
        },
        "equipment_slots": {
            "owner": "equipment",
            "primary_key": ["character_id", "slot_key"],
            "columns": {
                "character_id": column("TEXT"),
                "slot_key": column("TEXT", checks=("length(slot_key) > 0",)),
                "item_instance_id": column("TEXT"),
            },
            "foreign_keys": [
                foreign_key("character_id", "characters", "character_id", on_delete="CASCADE"),
                foreign_key("item_instance_id", "item_instances", "item_instance_id", on_delete="RESTRICT"),
            ],
            "unique": [["item_instance_id"]],
        },
        "item_reservations": {
            "owner": "inventory",
            "primary_key": ["reservation_id"],
            "columns": {
                "reservation_id": column("TEXT", generated_by="application_uuid"),
                "item_instance_id": column("TEXT"),
                "operation_id": column("TEXT"),
                "purpose_key": column("TEXT", checks=("length(purpose_key) > 0",)),
                "quantity": column("INTEGER", checks=("quantity > 0",)),
                "expires_at_utc": column("TEXT", nullable=True),
            },
            "foreign_keys": [
                foreign_key("item_instance_id", "item_instances", "item_instance_id", on_delete="CASCADE"),
                foreign_key("operation_id", "operation_records", "operation_id", on_delete="CASCADE"),
            ],
            "unique": [["operation_id", "item_instance_id"]],
        },
        "quest_progress": {
            "owner": "story",
            "primary_key": ["character_id", "quest_key"],
            "columns": {
                "character_id": column("TEXT"),
                "quest_key": column("TEXT", checks=("length(quest_key) > 0",)),
                "state_key": column("TEXT", checks=("state_key IN ('active','completed','failed','skipped')",)),
                "progress_json": column("TEXT", default="{}", checks=("json_valid(progress_json)",)),
                "completed_at_utc": column("TEXT", nullable=True),
                "version": column("INTEGER", default=0, checks=("version >= 0",)),
            },
            "foreign_keys": [foreign_key("character_id", "characters", "character_id", on_delete="CASCADE")],
            "checks": ["(state_key = 'completed' AND completed_at_utc IS NOT NULL) OR (state_key <> 'completed' AND completed_at_utc IS NULL)"],
        },
        "quest_item_balances": {
            "owner": "story",
            "primary_key": ["character_id", "item_key"],
            "columns": {
                "character_id": column("TEXT"),
                "item_key": column("TEXT", checks=("length(item_key) > 0",)),
                "quantity": column("INTEGER", default=0, checks=("quantity >= 0",)),
            },
            "foreign_keys": [foreign_key("character_id", "characters", "character_id", on_delete="CASCADE")],
        },
        "operation_records": {
            "owner": "application",
            "primary_key": ["operation_id"],
            "columns": {
                "operation_id": column("TEXT"),
                "operation_key": column("TEXT", checks=("length(operation_key) > 0",)),
                "aggregate_type": column("TEXT", checks=("length(aggregate_type) > 0",)),
                "aggregate_id": column("TEXT", checks=("length(aggregate_id) > 0",)),
                "status_key": column("TEXT", checks=("status_key IN ('in_progress','completed','failed')",)),
                "result_fingerprint": column("TEXT", nullable=True),
                "created_at_utc": column("TEXT"),
                "completed_at_utc": column("TEXT", nullable=True),
            },
            "unique": [["operation_id"]],
            "checks": ["(status_key = 'completed' AND completed_at_utc IS NOT NULL) OR (status_key <> 'completed' AND completed_at_utc IS NULL)"],
        },
        "domain_events": {
            "owner": "application",
            "primary_key": ["event_id"],
            "columns": {
                "event_id": column("TEXT"),
                "event_key": column("TEXT", checks=("length(event_key) > 0",)),
                "aggregate_type": column("TEXT", checks=("length(aggregate_type) > 0",)),
                "aggregate_id": column("TEXT", checks=("length(aggregate_id) > 0",)),
                "aggregate_version": column("INTEGER", checks=("aggregate_version >= 0",)),
                "sequence": column("INTEGER", checks=("sequence >= 0",)),
                "occurred_at_utc": column("TEXT"),
                "payload_json": column("TEXT", checks=("json_valid(payload_json)",)),
                "correlation_id": column("TEXT"),
                "causation_id": column("TEXT", nullable=True),
                "schema_version": column("INTEGER", default=1, checks=("schema_version >= 1",)),
            },
            "unique": [["aggregate_type", "aggregate_id", "aggregate_version", "sequence"]],
            "append_only": True,
        },
        "outbox_messages": {
            "owner": "infrastructure",
            "primary_key": ["message_id"],
            "columns": {
                "message_id": column("TEXT"),
                "event_id": column("TEXT"),
                "topic_key": column("TEXT", checks=("length(topic_key) > 0",)),
                "payload_json": column("TEXT", checks=("json_valid(payload_json)",)),
                "created_at_utc": column("TEXT"),
                "published_at_utc": column("TEXT", nullable=True),
                "attempt_count": column("INTEGER", default=0, checks=("attempt_count >= 0",)),
            },
            "foreign_keys": [foreign_key("event_id", "domain_events", "event_id", on_delete="RESTRICT")],
            "unique": [["event_id", "topic_key"]],
        },
        "schema_migrations": {
            "owner": "infrastructure",
            "primary_key": ["version"],
            "columns": {
                "version": column("INTEGER", checks=("version >= 1",)),
                "migration_key": column("TEXT", checks=("length(migration_key) > 0",)),
                "applied_at_utc": column("TEXT"),
                "checksum": column("TEXT", checks=("length(checksum) = 64",)),
            },
            "unique": [["migration_key"]],
            "append_only": True,
        },
    },
    "indexes": [
        {"name": "idx_characters_location", "table": "characters", "columns": ["location_key"], "unique": False},
        {"name": "idx_items_owner_definition", "table": "item_instances", "columns": ["owner_character_id", "definition_key"], "unique": False},
        {"name": "idx_quests_character_state", "table": "quest_progress", "columns": ["character_id", "state_key"], "unique": False},
        {"name": "idx_events_stream", "table": "domain_events", "columns": ["aggregate_type", "aggregate_id", "aggregate_version"], "unique": False},
        {"name": "idx_outbox_pending", "table": "outbox_messages", "columns": ["published_at_utc", "created_at_utc"], "unique": False},
        {"name": "idx_operations_aggregate", "table": "operation_records", "columns": ["aggregate_type", "aggregate_id"], "unique": False},
        {"name": "idx_reservations_expiry", "table": "item_reservations", "columns": ["expires_at_utc"], "unique": False},
    ],
    "deferred_domains": {
        "travel": {"decision": "deferred_no_placeholder_table", "future_owner": "world_travel"},
        "guild": {"decision": "deferred_no_placeholder_table", "future_owner": "social"},
        "direct_trade": {"decision": "deferred_no_placeholder_table", "future_owner": "social"},
        "auction": {"decision": "deferred_no_placeholder_table", "future_owner": "social"},
        "pvp_history": {"decision": "deferred_no_placeholder_table", "future_owner": "social"},
        "premium": {"decision": "deferred_no_placeholder_table", "future_owner": "economy"},
        "daily_rewards": {"decision": "deferred_no_placeholder_table", "future_owner": "events_auxiliary"},
        "notifications": {"decision": "deferred_no_placeholder_table", "future_owner": "events_auxiliary"},
        "ratings_chronicles": {"decision": "deferred_no_placeholder_table", "future_owner": "events_auxiliary"},
        "events": {"decision": "deferred_no_placeholder_table", "future_owner": "events_auxiliary"},
        "runes_sockets": {"decision": "deferred_no_placeholder_table", "future_owner": "inventory_equipment"},
    },
    "forbidden_designs": [
        "v1_migration_chain_copy",
        "v1_test_data_import",
        "sql_in_domain",
        "sql_in_handlers",
        "float_money",
        "localized_technical_keys",
        "critical_state_only_in_memory",
        "placeholder_tables_without_domain_contract",
    ],
}

SCHEMA_CONTRACT: Mapping[str, object] = MappingProxyType(_SCHEMA)
