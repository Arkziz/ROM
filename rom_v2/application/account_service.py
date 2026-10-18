"""Application service for transactional ROM V2 account lifecycle operations."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from rom_v2.application.account_ports import AccountUnitOfWorkFactoryPort
from rom_v2.domain.account import Account, AccountStatus


class AccountResultStatus(StrEnum):
    """Stable machine-readable use-case outcomes."""
    CREATED = "created"
    UPDATED = "updated"
    ALREADY_EXISTS = "already_exists"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"

@dataclass(frozen=True, slots=True)
class RegisterAccountCommand:
    """Carry deterministic account identity and canonical registration time."""
    account_id: str
    telegram_user_id: int
    registered_at_utc: str
    initial_bag_capacity: int = 60

@dataclass(frozen=True, slots=True)
class ChangeAccountStatusCommand:
    """Request one explicit account lifecycle transition."""
    account_id: str
    target_status: AccountStatus
    expected_version: int

@dataclass(frozen=True, slots=True)
class AccountCommandResult:
    """Return a machine outcome without presentation text."""
    status: AccountResultStatus
    reason: str
    account: Account | None

class AccountService:
    """Own account mutations through an application port, never infrastructure imports."""
    def __init__(self, unit_of_work_factory: AccountUnitOfWorkFactoryPort) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def register(self, command: RegisterAccountCommand) -> AccountCommandResult:
        """Create account and crystal wallet atomically or return the existing account."""
        try:
            candidate = Account(command.account_id, command.telegram_user_id, AccountStatus.ACTIVE, command.registered_at_utc, command.initial_bag_capacity)
        except ValueError as error:
            return AccountCommandResult(AccountResultStatus.REJECTED, str(error), None)
        with self._unit_of_work_factory() as unit:
            existing = unit.accounts.find_by_telegram_user_id(candidate.telegram_user_id)
            if existing is not None:
                return AccountCommandResult(AccountResultStatus.ALREADY_EXISTS, "telegram_identity_exists", existing)
            if unit.accounts.find_by_id(candidate.account_id) is not None:
                return AccountCommandResult(AccountResultStatus.REJECTED, "account_id_exists", None)
            unit.accounts.add(candidate)
            unit.accounts.create_crystal_wallet(candidate.account_id)
            unit.commit()
        return AccountCommandResult(AccountResultStatus.CREATED, "account_created", candidate)

    def change_status(self, command: ChangeAccountStatusCommand) -> AccountCommandResult:
        """Apply an optimistic lifecycle transition inside one transaction."""
        with self._unit_of_work_factory() as unit:
            current = unit.accounts.find_by_id(command.account_id)
            if current is None:
                return AccountCommandResult(AccountResultStatus.NOT_FOUND, "account_not_found", None)
            if current.version != command.expected_version:
                return AccountCommandResult(AccountResultStatus.REJECTED, "account_version_conflict", current)
            try:
                updated = current.change_status(command.target_status)
            except ValueError as error:
                return AccountCommandResult(AccountResultStatus.REJECTED, str(error), current)
            if updated == current:
                return AccountCommandResult(AccountResultStatus.UPDATED, "account_status_unchanged", current)
            unit.accounts.update_status(updated, expected_version=command.expected_version)
            unit.commit()
        return AccountCommandResult(AccountResultStatus.UPDATED, "account_status_updated", updated)
