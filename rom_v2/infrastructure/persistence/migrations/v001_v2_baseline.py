"""Migration 001: create the clean ROM V2 baseline schema."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    """Describe one immutable ordered SQLite migration."""

    version: int
    key: str
    sql: str

    @property
    def checksum(self) -> str:
        """Return the stable SHA-256 checksum of the migration SQL."""
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


BASELINE_SQL = r"""
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY NOT NULL CHECK (length(account_id) > 0),
    telegram_user_id INTEGER NOT NULL UNIQUE CHECK (telegram_user_id > 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','blocked','closed')),
    registered_at_utc TEXT NOT NULL CHECK (length(registered_at_utc) > 0),
    bag_capacity INTEGER NOT NULL DEFAULT 60 CHECK (bag_capacity BETWEEN 1 AND 1000),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0)
) STRICT;

CREATE TABLE characters (
    character_id TEXT PRIMARY KEY NOT NULL CHECK (length(character_id) > 0),
    account_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) BETWEEN 1 AND 64),
    class_key TEXT NOT NULL CHECK (length(class_key) > 0),
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1),
    experience INTEGER NOT NULL DEFAULT 0 CHECK (experience >= 0),
    location_key TEXT NOT NULL CHECK (length(location_key) > 0),
    current_hp INTEGER NOT NULL CHECK (current_hp >= 0),
    current_mp INTEGER CHECK (current_mp IS NULL OR current_mp >= 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE character_primary_stats (
    character_id TEXT PRIMARY KEY NOT NULL,
    strength INTEGER NOT NULL CHECK (strength >= 0),
    dexterity INTEGER NOT NULL CHECK (dexterity >= 0),
    intelligence INTEGER NOT NULL CHECK (intelligence >= 0),
    wisdom INTEGER NOT NULL CHECK (wisdom >= 0),
    stamina INTEGER NOT NULL CHECK (stamina >= 0),
    unspent_points INTEGER NOT NULL DEFAULT 0 CHECK (unspent_points >= 0),
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE gold_wallets (
    character_id TEXT PRIMARY KEY NOT NULL,
    balance_minor INTEGER NOT NULL DEFAULT 0 CHECK (balance_minor >= 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE crystal_wallets (
    account_id TEXT PRIMARY KEY NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE operation_records (
    operation_id TEXT PRIMARY KEY NOT NULL,
    operation_key TEXT NOT NULL CHECK (length(operation_key) > 0),
    aggregate_type TEXT NOT NULL CHECK (length(aggregate_type) > 0),
    aggregate_id TEXT NOT NULL CHECK (length(aggregate_id) > 0),
    status_key TEXT NOT NULL CHECK (status_key IN ('in_progress','completed','failed')),
    result_fingerprint TEXT,
    created_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    CHECK ((status_key = 'completed' AND completed_at_utc IS NOT NULL) OR (status_key <> 'completed' AND completed_at_utc IS NULL))
) STRICT;

CREATE TABLE crystal_ledger (
    entry_id TEXT PRIMARY KEY NOT NULL,
    account_id TEXT NOT NULL,
    operation_id TEXT NOT NULL UNIQUE,
    amount INTEGER NOT NULL CHECK (amount <> 0),
    reason_key TEXT NOT NULL CHECK (length(reason_key) > 0),
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (operation_id) REFERENCES operation_records(operation_id) ON DELETE RESTRICT ON UPDATE CASCADE
) STRICT;

CREATE TABLE item_instances (
    item_instance_id TEXT PRIMARY KEY NOT NULL,
    definition_key TEXT NOT NULL CHECK (length(definition_key) > 0),
    owner_character_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    durability INTEGER CHECK (durability IS NULL OR durability BETWEEN 0 AND 100),
    enhancement_level INTEGER NOT NULL DEFAULT 0 CHECK (enhancement_level >= 0),
    binding_key TEXT NOT NULL DEFAULT 'unbound' CHECK (length(binding_key) > 0),
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    FOREIGN KEY (owner_character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE equipment_slots (
    character_id TEXT NOT NULL,
    slot_key TEXT NOT NULL CHECK (length(slot_key) > 0),
    item_instance_id TEXT NOT NULL UNIQUE,
    PRIMARY KEY (character_id, slot_key),
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (item_instance_id) REFERENCES item_instances(item_instance_id) ON DELETE RESTRICT ON UPDATE CASCADE
) STRICT;

CREATE TABLE item_reservations (
    reservation_id TEXT PRIMARY KEY NOT NULL,
    item_instance_id TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    purpose_key TEXT NOT NULL CHECK (length(purpose_key) > 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    expires_at_utc TEXT,
    UNIQUE (operation_id, item_instance_id),
    FOREIGN KEY (item_instance_id) REFERENCES item_instances(item_instance_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (operation_id) REFERENCES operation_records(operation_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE quest_progress (
    character_id TEXT NOT NULL,
    quest_key TEXT NOT NULL CHECK (length(quest_key) > 0),
    state_key TEXT NOT NULL CHECK (state_key IN ('active','completed','failed','skipped')),
    progress_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(progress_json)),
    completed_at_utc TEXT,
    version INTEGER NOT NULL DEFAULT 0 CHECK (version >= 0),
    PRIMARY KEY (character_id, quest_key),
    CHECK ((state_key = 'completed' AND completed_at_utc IS NOT NULL) OR (state_key <> 'completed' AND completed_at_utc IS NULL)),
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE quest_item_balances (
    character_id TEXT NOT NULL,
    item_key TEXT NOT NULL CHECK (length(item_key) > 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (character_id, item_key),
    FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE ON UPDATE CASCADE
) STRICT;

CREATE TABLE domain_events (
    event_id TEXT PRIMARY KEY NOT NULL,
    event_key TEXT NOT NULL CHECK (length(event_key) > 0),
    aggregate_type TEXT NOT NULL CHECK (length(aggregate_type) > 0),
    aggregate_id TEXT NOT NULL CHECK (length(aggregate_id) > 0),
    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 0),
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    occurred_at_utc TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version >= 1),
    UNIQUE (aggregate_type, aggregate_id, aggregate_version, sequence)
) STRICT;

CREATE TABLE outbox_messages (
    message_id TEXT PRIMARY KEY NOT NULL,
    event_id TEXT NOT NULL,
    topic_key TEXT NOT NULL CHECK (length(topic_key) > 0),
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    created_at_utc TEXT NOT NULL,
    published_at_utc TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    UNIQUE (event_id, topic_key),
    FOREIGN KEY (event_id) REFERENCES domain_events(event_id) ON DELETE RESTRICT ON UPDATE CASCADE
) STRICT;

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY NOT NULL CHECK (version >= 1),
    migration_key TEXT NOT NULL UNIQUE CHECK (length(migration_key) > 0),
    applied_at_utc TEXT NOT NULL,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64)
) STRICT;

CREATE INDEX idx_characters_location ON characters(location_key);
CREATE INDEX idx_items_owner_definition ON item_instances(owner_character_id, definition_key);
CREATE INDEX idx_quests_character_state ON quest_progress(character_id, state_key);
CREATE INDEX idx_events_stream ON domain_events(aggregate_type, aggregate_id, aggregate_version);
CREATE INDEX idx_outbox_pending ON outbox_messages(published_at_utc, created_at_utc);
CREATE INDEX idx_operations_aggregate ON operation_records(aggregate_type, aggregate_id);
CREATE INDEX idx_reservations_expiry ON item_reservations(expires_at_utc);
""".strip()

MIGRATION = Migration(version=1, key="001_v2_baseline", sql=BASELINE_SQL)
