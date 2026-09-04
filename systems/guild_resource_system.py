# -*- coding: utf-8 -*-
"""Read-only guild-resource design surface for Stage 18.8.1.

No function in this module writes to game.db or activates a future sink.
"""
from __future__ import annotations

from copy import deepcopy

from data.guild_resource_policy import (
    GUILD_RESOURCE_FUTURE_INVARIANTS,
    GUILD_RESOURCE_INITIAL_SPEND_ROLE,
    GUILD_RESOURCE_POLICY_VERSION,
    GUILD_RESOURCE_SINKS,
    GUILD_RESOURCE_SPENDING_ENABLED,
)

GUILD_RESOURCE_INACTIVE_MESSAGE = (
    "Використання ресурсу гільдії ще не активовано. "
    "Можливості перебувають на етапі проєктування."
)


def get_guild_resource_design_policy():
    """Return a detached read-only snapshot of the future policy."""
    return {
        "version": GUILD_RESOURCE_POLICY_VERSION,
        "spending_enabled": GUILD_RESOURCE_SPENDING_ENABLED,
        "initial_spend_role": GUILD_RESOURCE_INITIAL_SPEND_ROLE,
        "sinks": deepcopy(GUILD_RESOURCE_SINKS),
        "invariants": tuple(GUILD_RESOURCE_FUTURE_INVARIANTS),
    }


def get_guild_resource_sink_definition(sink_key):
    key = str(sink_key or "").strip()
    for sink in GUILD_RESOURCE_SINKS:
        if sink["key"] == key:
            return deepcopy(sink)
    return None


def validate_guild_resource_feature_inactive():
    return {
        "success": False,
        "enabled": False,
        "code": "guild_resource_spending_inactive",
        "message": GUILD_RESOURCE_INACTIVE_MESSAGE,
    }


def spend_guild_resource(*args, **kwargs):
    """Fail closed until an approved transactional implementation exists."""
    return validate_guild_resource_feature_inactive()


def activate_guild_resource_sink(*args, **kwargs):
    """Fail closed until an approved transactional implementation exists."""
    return validate_guild_resource_feature_inactive()
