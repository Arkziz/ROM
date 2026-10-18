"""Account aggregate and stable lifecycle values for ROM V2."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum


class AccountStatus(StrEnum):
    """Stable technical account lifecycle keys, independent of presentation text."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class Account:
    """Represent account-level identity, lifecycle, bag capacity, and version."""

    account_id: str
    telegram_user_id: int
    status: AccountStatus
    registered_at_utc: str
    bag_capacity: int
    version: int = 0

    def __post_init__(self) -> None:
        """Enforce schema-aligned invariants before persistence."""
        if not self.account_id.strip():
            raise ValueError("account_id_required")
        if self.telegram_user_id <= 0:
            raise ValueError("telegram_user_id_must_be_positive")
        if not 1 <= self.bag_capacity <= 1000:
            raise ValueError("bag_capacity_out_of_range")
        if self.version < 0:
            raise ValueError("account_version_must_be_non_negative")
        try:
            parsed = datetime.fromisoformat(self.registered_at_utc.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("registered_at_utc_invalid") from error
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError("registered_at_utc_must_be_utc")

    def change_status(self, target: AccountStatus) -> Account:
        """Return the next aggregate state under explicit lifecycle rules."""
        if self.status == target:
            return self
        allowed = {
            AccountStatus.ACTIVE: {AccountStatus.BLOCKED, AccountStatus.CLOSED},
            AccountStatus.BLOCKED: {AccountStatus.ACTIVE, AccountStatus.CLOSED},
            AccountStatus.CLOSED: set(),
        }
        if target not in allowed[self.status]:
            raise ValueError("account_status_transition_forbidden")
        return replace(self, status=target, version=self.version + 1)
