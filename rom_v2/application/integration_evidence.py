"""Machine-readable integration evidence levels for deferred V2 consumers.

A shared application API exists for profile, combat, and simulator stat snapshots.
Concrete adapters, runtime dispatch, and end-to-end acceptance remain deferred to the
corresponding roadmap stages and must not be inferred from API availability.
"""
from __future__ import annotations

SNAPSHOT_INTEGRATION_EVIDENCE_LEVEL = "API_READY"
SNAPSHOT_CONSUMER_WIRING = {
    "profile": "DEFERRED",
    "combat": "DEFERRED",
    "simulator": "DEFERRED",
}
SNAPSHOT_ADAPTER_CONNECTED = False
SNAPSHOT_RUNTIME_DISPATCH_VERIFIED = False
SNAPSHOT_END_TO_END_ACCEPTED = False
