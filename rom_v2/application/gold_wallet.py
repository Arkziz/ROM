"""Pure API-ready Gold Wallet service for ROM V2.

Money is Decimal-only and quantized to two places with ROUND_HALF_UP. Persistence,
SQLite, runtime and presentation adapters are intentionally outside this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Protocol

GOLD_QUANTUM = Decimal("0.01")


class GoldWalletContractError(ValueError):
    """Raised when a wallet command violates the public contract."""


class GoldWalletConflictError(GoldWalletContractError):
    """Raised when one operation key is replayed with a different payload."""


class GoldDirection(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True, slots=True)
class GoldWalletCommand:
    """Stable, presentation-free request for one exact wallet mutation."""

    operation_key: str
    account_id: int
    direction: GoldDirection
    amount: Decimal
    reason_code: str


@dataclass(frozen=True, slots=True)
class GoldWalletOperation:
    """Immutable audit record persisted atomically with the balance."""

    operation_key: str
    account_id: int
    direction: GoldDirection
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reason_code: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class GoldWalletResult:
    operation: GoldWalletOperation
    replayed: bool


class GoldWalletRepositoryPort(Protocol):
    def get_balance(self, account_id: int) -> Decimal: ...
    def set_balance(self, account_id: int, balance: Decimal) -> None: ...
    def get_operation(self, operation_key: str) -> GoldWalletOperation | None: ...
    def add_operation(self, operation: GoldWalletOperation) -> None: ...


class GoldWalletUnitOfWorkPort(Protocol):
    wallet: GoldWalletRepositoryPort
    def now(self) -> datetime: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


def normalize_gold(value: Decimal) -> Decimal:
    """Validate and quantize Decimal money without accepting float input."""
    if not isinstance(value, Decimal):
        raise GoldWalletContractError("amount_must_be_decimal")
    if not value.is_finite():
        raise GoldWalletContractError("amount_must_be_finite")
    try:
        return value.quantize(GOLD_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise GoldWalletContractError("amount_cannot_be_quantized") from exc


class GoldWalletService:
    """Canonical V2 owner for atomic, idempotent gold mutations."""

    def execute(self, command: GoldWalletCommand, unit_of_work: GoldWalletUnitOfWorkPort) -> GoldWalletResult:
        normalized = self._validate_command(command)
        canonical = GoldWalletCommand(
            operation_key=command.operation_key,
            account_id=command.account_id,
            direction=command.direction,
            amount=normalized,
            reason_code=command.reason_code,
        )
        try:
            existing = unit_of_work.wallet.get_operation(canonical.operation_key)
            if existing is not None:
                if not self._same_payload(existing, canonical):
                    raise GoldWalletConflictError("operation_key_payload_conflict")
                return GoldWalletResult(existing, replayed=True)

            before = normalize_gold(unit_of_work.wallet.get_balance(canonical.account_id))
            if before < Decimal("0.00"):
                raise GoldWalletContractError("stored_balance_is_negative")
            after = before + canonical.amount if canonical.direction is GoldDirection.CREDIT else before - canonical.amount
            after = normalize_gold(after)
            if after < Decimal("0.00"):
                raise GoldWalletContractError("insufficient_funds")

            operation = GoldWalletOperation(
                operation_key=canonical.operation_key,
                account_id=canonical.account_id,
                direction=canonical.direction,
                amount=canonical.amount,
                balance_before=before,
                balance_after=after,
                reason_code=canonical.reason_code,
                created_at=unit_of_work.now(),
            )
            unit_of_work.wallet.set_balance(canonical.account_id, after)
            unit_of_work.wallet.add_operation(operation)
            unit_of_work.commit()
            return GoldWalletResult(operation, replayed=False)
        except Exception:
            unit_of_work.rollback()
            raise

    @staticmethod
    def _validate_command(command: GoldWalletCommand) -> Decimal:
        if not command.operation_key or not command.operation_key.strip():
            raise GoldWalletContractError("operation_key_required")
        if command.account_id <= 0:
            raise GoldWalletContractError("account_id_must_be_positive")
        if not isinstance(command.direction, GoldDirection):
            raise GoldWalletContractError("invalid_direction")
        if not command.reason_code or not command.reason_code.strip():
            raise GoldWalletContractError("reason_code_required")
        amount = normalize_gold(command.amount)
        if amount <= Decimal("0.00"):
            raise GoldWalletContractError("amount_must_be_positive")
        return amount

    @staticmethod
    def _same_payload(existing: GoldWalletOperation, command: GoldWalletCommand) -> bool:
        return (
            existing.account_id == command.account_id
            and existing.direction is command.direction
            and existing.amount == command.amount
            and existing.reason_code == command.reason_code
        )
