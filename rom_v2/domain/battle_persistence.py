"""Pure PvE encounter lifecycle persistence contract for ROM V2.

This module models only the V1-confirmed lifecycle marker. It intentionally
contains no database, repository, Telegram, wall-clock, or full battle snapshot
logic. Callers persist returned immutable state through later application and
infrastructure stages.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class BattlePersistenceContractFailure(ValueError):
    """Raised when a lifecycle command violates the bounded contract."""


class PersistedEncounterStatus(str, Enum):
    ACTIVE = "active"
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPE = "escape"
    EXPIRED = "expired"


class PersistedEncounterTerminalOutcome(str, Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    ESCAPE = "escape"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class PersistedEncounterMarker:
    """Immutable lifecycle marker, not a serialized mutable battle aggregate."""

    encounter_id: str
    actor_id: str
    started_at: datetime
    expires_at: datetime
    status: PersistedEncounterStatus = PersistedEncounterStatus.ACTIVE
    terminal_operation_id: str | None = None
    terminal_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.encounter_id.strip() or not self.actor_id.strip():
            raise BattlePersistenceContractFailure("encounter_id_and_actor_id_required")
        for name, value in (("started_at", self.started_at), ("expires_at", self.expires_at)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise BattlePersistenceContractFailure(f"{name}_must_be_timezone_aware")
        if self.expires_at <= self.started_at:
            raise BattlePersistenceContractFailure("expires_at_must_follow_started_at")
        terminal = self.status is not PersistedEncounterStatus.ACTIVE
        if terminal != bool(self.terminal_operation_id and self.terminal_at):
            raise BattlePersistenceContractFailure("terminal_metadata_must_match_status")

    @property
    def is_active(self) -> bool:
        return self.status is PersistedEncounterStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class EncounterPersistenceResult:
    marker: PersistedEncounterMarker
    accepted: bool
    duplicate: bool
    reason: str


def _aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise BattlePersistenceContractFailure(f"{name}_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def begin_persisted_encounter(encounter_id: str, actor_id: str, started_at: datetime, expires_at: datetime) -> PersistedEncounterMarker:
    """Create one active marker; repository-level actor uniqueness is deferred."""
    return PersistedEncounterMarker(encounter_id.strip(), actor_id.strip(), _aware(started_at, "started_at"), _aware(expires_at, "expires_at"))


def find_active_persisted_encounter(markers: Iterable[PersistedEncounterMarker], actor_id: str) -> PersistedEncounterMarker | None:
    """Return the sole active marker for an actor and fail closed on duplicates."""
    active = [m for m in markers if m.actor_id == actor_id and m.is_active]
    if len(active) > 1:
        raise BattlePersistenceContractFailure("multiple_active_encounters_for_actor")
    return active[0] if active else None


def claim_persisted_encounter_terminal(marker: PersistedEncounterMarker, outcome: PersistedEncounterTerminalOutcome, operation_id: str, occurred_at: datetime) -> EncounterPersistenceResult:
    """Claim one absorbing terminal outcome with operation-id idempotency."""
    operation_id = operation_id.strip()
    if not operation_id:
        raise BattlePersistenceContractFailure("operation_id_required")
    occurred = _aware(occurred_at, "occurred_at")
    if marker.is_active:
        updated = replace(marker, status=PersistedEncounterStatus(outcome.value), terminal_operation_id=operation_id, terminal_at=occurred)
        return EncounterPersistenceResult(updated, True, False, "terminal_claimed")
    duplicate = marker.terminal_operation_id == operation_id and marker.status.value == outcome.value
    return EncounterPersistenceResult(marker, False, duplicate, "duplicate_terminal_claim" if duplicate else "already_terminal")


def select_expired_persisted_encounters(markers: Iterable[PersistedEncounterMarker], now: datetime) -> tuple[PersistedEncounterMarker, ...]:
    """Select active markers whose configured expiry instant has been reached."""
    instant = _aware(now, "now")
    return tuple(sorted((m for m in markers if m.is_active and m.expires_at <= instant), key=lambda m: (m.expires_at, m.encounter_id)))


def expire_persisted_encounter_once(marker: PersistedEncounterMarker, now: datetime) -> EncounterPersistenceResult:
    """Expire an eligible marker through the same exactly-once terminal claim."""
    instant = _aware(now, "now")
    if not marker.is_active:
        return EncounterPersistenceResult(marker, False, marker.status is PersistedEncounterStatus.EXPIRED, "already_terminal")
    if marker.expires_at > instant:
        return EncounterPersistenceResult(marker, False, False, "not_expired")
    return claim_persisted_encounter_terminal(marker, PersistedEncounterTerminalOutcome.EXPIRED, f"expire:{marker.encounter_id}", instant)


def recover_persisted_encounters_after_restart(markers: Iterable[PersistedEncounterMarker], now: datetime) -> tuple[EncounterPersistenceResult, ...]:
    """Apply V1-equivalent stale expiry/cleanup, never exact battle resumption."""
    return tuple(expire_persisted_encounter_once(marker, now) for marker in select_expired_persisted_encounters(markers, now))
