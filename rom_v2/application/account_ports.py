"""Application ports for account persistence and transaction ownership."""
from __future__ import annotations

from typing import Protocol

from rom_v2.domain.account import Account


class AccountRepositoryPort(Protocol):
    """Describe account persistence needed by application use cases."""

    def find_by_id(self, account_id: str) -> Account | None: ...
    def find_by_telegram_user_id(self, telegram_user_id: int) -> Account | None: ...
    def add(self, account: Account) -> None: ...
    def create_crystal_wallet(self, account_id: str) -> None: ...
    def update_status(self, account: Account, *, expected_version: int) -> None: ...


class AccountUnitOfWorkPort(Protocol):
    """Expose account repositories and explicit transaction terminal operations."""

    accounts: AccountRepositoryPort
    def __enter__(self) -> AccountUnitOfWorkPort: ...
    def __exit__(self, exception_type, exception, traceback) -> bool: ...
    def commit(self) -> None: ...


class AccountUnitOfWorkFactoryPort(Protocol):
    """Create a fresh one-shot account Unit of Work per operation."""

    def __call__(self) -> AccountUnitOfWorkPort: ...
