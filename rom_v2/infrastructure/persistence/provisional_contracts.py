"""Governance contract for gameplay tables created before their domain audits.

The listed tables physically exist in the clean V2 baseline, but their columns,
constraints, and lifecycle actions are provisional. Domain repositories must not use
them until the corresponding V1 audit has completed and a later migration has
reconciled or explicitly accepted the table contract.
"""
from __future__ import annotations

PROVISIONAL_CONTRACT_STATUS = "PROVISIONAL_RESERVED"
PROVISIONAL_GAMEPLAY_TABLES = frozenset(
    {
        "item_instances",
        "equipment_slots",
        "item_reservations",
        "quest_progress",
        "quest_item_balances",
    }
)


def is_provisional_gameplay_table(table_name: str) -> bool:
    """Return whether a table is reserved but not authoritative V1 parity."""
    return str(table_name).casefold() in PROVISIONAL_GAMEPLAY_TABLES


def require_authoritative_gameplay_table(table_name: str) -> None:
    """Fail closed when production code tries to use an unaudited table contract."""
    if is_provisional_gameplay_table(table_name):
        raise RuntimeError("provisional_persistence_contract")
