"""SQLite repository for V1-faithful account registration state."""
from __future__ import annotations
import sqlite3
from rom_v2.domain.account import Account
from rom_v2.infrastructure.persistence.repository_base import SQLiteRepositoryBase
class SQLiteAccountRepository(SQLiteRepositoryBase):
 @staticmethod
 def _map(row:sqlite3.Row)->Account:return Account(str(row["account_id"]),int(row["telegram_user_id"]),str(row["registered_at_utc"]),int(row["bag_capacity"]))
 def find_by_id(self,account_id:str)->Account|None:
  row=self.fetch_one("SELECT * FROM accounts WHERE account_id = ?",(account_id,));return None if row is None else self._map(row)
 def find_by_telegram_user_id(self,telegram_user_id:int)->Account|None:
  row=self.fetch_one("SELECT * FROM accounts WHERE telegram_user_id = ?",(telegram_user_id,));return None if row is None else self._map(row)
 def add(self,account:Account)->None:
  changed=self.execute("INSERT INTO accounts(account_id,telegram_user_id,registered_at_utc,bag_capacity) VALUES (?,?,?,?)",(account.account_id,account.telegram_user_id,account.registered_at_utc,account.bag_capacity));self.require_exact_rowcount(changed)
 def create_crystal_wallet(self,account_id:str)->None:
  changed=self.execute("INSERT INTO crystal_wallets(account_id,balance) VALUES (?,0)",(account_id,));self.require_exact_rowcount(changed)
