"""Canonical SQLite repository for the ROM V2 account aggregate."""
from __future__ import annotations

import sqlite3

from rom_v2.domain.account import Account, AccountStatus
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase


class SQLiteAccountRepository(SQLiteRepositoryBase):
    """Map accounts and account-level crystal-wallet initialization in one UoW."""

    @staticmethod
    def _map(row: sqlite3.Row) -> Account:
        return Account(
            account_id=str(row["account_id"]),
            telegram_user_id=int(row["telegram_user_id"]),
            status=AccountStatus(str(row["status"])),
            registered_at_utc=str(row["registered_at_utc"]),
            bag_capacity=int(row["bag_capacity"]),
            version=int(row["version"]),
        )

    def find_by_id(self, account_id: str) -> Account | None:
        row = self.fetch_one("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
        return None if row is None else self._map(row)

    def find_by_telegram_user_id(self, telegram_user_id: int) -> Account | None:
        row = self.fetch_one("SELECT * FROM accounts WHERE telegram_user_id = ?", (telegram_user_id,))
        return None if row is None else self._map(row)

    def add(self, account: Account) -> None:
        changed = self.execute(
            "INSERT INTO accounts(account_id,telegram_user_id,status,registered_at_utc,bag_capacity,version) VALUES (?,?,?,?,?,?)",
            (account.account_id, account.telegram_user_id, account.status.value, account.registered_at_utc, account.bag_capacity, account.version),
        )
        self.require_exact_rowcount(changed)

    def create_crystal_wallet(self, account_id: str) -> None:
        changed = self.execute("INSERT INTO crystal_wallets(account_id,balance,version) VALUES (?,0,0)", (account_id,))
        self.require_exact_rowcount(changed)

    def update_status(self, account: Account, *, expected_version: int) -> None:
        changed = self.execute(
            "UPDATE accounts SET status = ?, version = ? WHERE account_id = ? AND version = ?",
            (account.status.value, account.version, account.account_id, expected_version),
        )
        self.require_exact_rowcount(changed)
