"""Deterministic API-ready inactivity-reminder evaluation service."""
from __future__ import annotations

from datetime import datetime, timedelta

from .model import (
    DEFAULT_INACTIVITY_THRESHOLD,
    InactivityReminderDecision,
    InactivityReminderReceipt,
    aware_utc,
    build_cycle_key,
)


class InactivityReminderService:
    """Evaluate seven-full-day cycles without inventing scheduler/delivery policy."""

    def __init__(self, threshold: timedelta = DEFAULT_INACTIVITY_THRESHOLD) -> None:
        if threshold != DEFAULT_INACTIVITY_THRESHOLD:
            raise ValueError("unsupported_inactivity_threshold")
        self._threshold = threshold

    @property
    def threshold(self) -> timedelta:
        return self._threshold

    def evaluate(
        self,
        *,
        user_id: int,
        last_activity_at: datetime,
        evaluated_at: datetime,
        delivered_cycle_keys: frozenset[str] = frozenset(),
    ) -> InactivityReminderDecision:
        """Evaluate exactly one cycle from injected activity, clock and audit state."""
        activity = aware_utc(last_activity_at, "last_activity_at")
        current = aware_utc(evaluated_at, "evaluated_at")
        cycle_key = build_cycle_key(user_id, activity)
        due_at = activity + self._threshold
        delivered = cycle_key in delivered_cycle_keys
        return InactivityReminderDecision(
            user_id=user_id,
            last_activity_at=activity,
            evaluated_at=current,
            due_at=due_at,
            cycle_key=cycle_key,
            due=current >= due_at and not delivered,
            already_delivered=delivered,
        )

    def receipt_after_successful_delivery(
        self,
        decision: InactivityReminderDecision,
        *,
        delivered_at: datetime,
    ) -> InactivityReminderReceipt:
        """Build audit data only after an external adapter confirms delivery success."""
        if not decision.due or decision.already_delivered:
            raise ValueError("reminder_cycle_not_deliverable")
        delivered = aware_utc(delivered_at, "delivered_at")
        if delivered < decision.due_at:
            raise ValueError("delivered_at_precedes_due_at")
        return InactivityReminderReceipt(
            user_id=decision.user_id,
            cycle_key=decision.cycle_key,
            last_activity_at=decision.last_activity_at,
            delivered_at=delivered,
        )
