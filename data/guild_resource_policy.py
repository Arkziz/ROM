# -*- coding: utf-8 -*-
"""Inactive design registry for future guild-resource uses.

Stage 18.8.1 intentionally activates no spending, buffs, storage or upgrades.
"""
from __future__ import annotations

GUILD_RESOURCE_POLICY_VERSION = "18.8.1"
GUILD_RESOURCE_SPENDING_ENABLED = False
GUILD_RESOURCE_INITIAL_SPEND_ROLE = "leader"
GUILD_RESOURCE_SINK_STATUS_PLANNED = "planned"
GUILD_RESOURCE_SINK_STATUS_DEFERRED = "deferred"

GUILD_RESOURCE_SINKS = (
    {
        "key": "member_limit",
        "title": "Розширення ліміту учасників",
        "status": GUILD_RESOURCE_SINK_STATUS_PLANNED,
        "order": 1,
        "combat_impact": False,
        "requires": (),
    },
    {
        "key": "guild_storage_unlock",
        "title": "Відкриття складу гільдії",
        "status": GUILD_RESOURCE_SINK_STATUS_PLANNED,
        "order": 2,
        "combat_impact": False,
        "requires": ("approved_guild_level", "storage_domain"),
    },
    {
        "key": "guild_storage_capacity",
        "title": "Розширення місткості складу",
        "status": GUILD_RESOURCE_SINK_STATUS_PLANNED,
        "order": 3,
        "combat_impact": False,
        "requires": ("guild_storage_unlock",),
    },
    {
        "key": "attack_buff",
        "title": "Тимчасовий бонус фізичної та магічної атаки",
        "status": GUILD_RESOURCE_SINK_STATUS_DEFERRED,
        "order": 4,
        "combat_impact": True,
        "requires": ("stage_18_12_to_18_21_balance_complete",),
    },
    {
        "key": "defense_buff",
        "title": "Тимчасовий бонус фізичного та магічного захисту",
        "status": GUILD_RESOURCE_SINK_STATUS_DEFERRED,
        "order": 5,
        "combat_impact": True,
        "requires": ("stage_18_12_to_18_21_balance_complete",),
    },
    {
        "key": "health_buff",
        "title": "Тимчасовий бонус максимального здоров'я",
        "status": GUILD_RESOURCE_SINK_STATUS_DEFERRED,
        "order": 6,
        "combat_impact": True,
        "requires": ("stage_18_12_to_18_21_balance_complete",),
    },
)

GUILD_RESOURCE_FUTURE_INVARIANTS = (
    "resource_cannot_be_negative",
    "leader_authorization_rechecked_in_transaction",
    "server_authoritative_price_and_eligibility",
    "idempotency_key_charged_at_most_once",
    "immutable_debit_audit_record",
    "failed_activation_rolls_back_debit_and_state",
    "restart_cannot_duplicate_activation",
)
