"""Application service for V1-faithful ROM V2 account registration."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from rom_v2.application.account_ports import AccountUnitOfWorkFactoryPort
from rom_v2.domain.account import Account
class AccountResultStatus(StrEnum):CREATED="created";ALREADY_EXISTS="already_exists";REJECTED="rejected"
@dataclass(frozen=True,slots=True)
class RegisterAccountCommand:
 account_id:str;telegram_user_id:int;registered_at_utc:str;initial_bag_capacity:int
@dataclass(frozen=True,slots=True)
class AccountCommandResult:
 status:AccountResultStatus;reason:str;account:Account|None
class AccountService:
 """Create accounts and zero crystal wallets atomically and idempotently."""
 def __init__(self,unit_of_work_factory:AccountUnitOfWorkFactoryPort)->None:self._unit_of_work_factory=unit_of_work_factory
 def register(self,command:RegisterAccountCommand)->AccountCommandResult:
  try:candidate=Account(command.account_id,command.telegram_user_id,command.registered_at_utc,command.initial_bag_capacity)
  except ValueError as error:return AccountCommandResult(AccountResultStatus.REJECTED,str(error),None)
  with self._unit_of_work_factory() as unit:
   existing=unit.accounts.find_by_telegram_user_id(candidate.telegram_user_id)
   if existing is not None:return AccountCommandResult(AccountResultStatus.ALREADY_EXISTS,"telegram_identity_exists",existing)
   if unit.accounts.find_by_id(candidate.account_id) is not None:return AccountCommandResult(AccountResultStatus.REJECTED,"account_id_exists",None)
   unit.accounts.add(candidate);unit.accounts.create_crystal_wallet(candidate.account_id);unit.commit()
  return AccountCommandResult(AccountResultStatus.CREATED,"account_created",candidate)
