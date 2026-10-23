"""Pure API-ready Crystal Wallet/Ledger service for ROM V2."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

class CrystalWalletContractError(ValueError): pass
class CrystalWalletConflictError(CrystalWalletContractError): pass
class CrystalDirection(str, Enum):
    CREDIT="credit"
    DEBIT="debit"

@dataclass(frozen=True, slots=True)
class CrystalWalletCommand:
    idempotency_key: str
    user_id: int
    direction: CrystalDirection
    amount: int
    reason_code: str
    source: str

@dataclass(frozen=True, slots=True)
class CrystalLedgerTransaction:
    transaction_id: str
    idempotency_key: str
    user_id: int
    direction: CrystalDirection
    amount: int
    balance_before: int
    balance_after: int
    reason_code: str
    source: str
    original_transaction_id: str | None
    created_at: datetime

@dataclass(frozen=True, slots=True)
class CrystalWalletResult:
    transaction: CrystalLedgerTransaction
    replayed: bool

class CrystalWalletRepositoryPort(Protocol):
    def get_balance(self,user_id:int)->int: ...
    def set_balance(self,user_id:int,balance:int)->None: ...
    def get_by_idempotency_key(self,key:str)->CrystalLedgerTransaction|None: ...
    def get_transaction(self,transaction_id:str)->CrystalLedgerTransaction|None: ...
    def get_compensation(self,original_transaction_id:str)->CrystalLedgerTransaction|None: ...
    def append_transaction(self,transaction:CrystalLedgerTransaction)->None: ...

class CrystalWalletUnitOfWorkPort(Protocol):
    wallet: CrystalWalletRepositoryPort
    def next_transaction_id(self)->str: ...
    def now(self)->datetime: ...
    def commit(self)->None: ...
    def rollback(self)->None: ...

class CrystalWalletLedgerService:
    """Canonical owner for integer crystal mutation and append-only history."""
    def execute(self,command:CrystalWalletCommand,uow:CrystalWalletUnitOfWorkPort)->CrystalWalletResult:
        self._validate(command)
        try:
            existing=uow.wallet.get_by_idempotency_key(command.idempotency_key)
            if existing is not None:
                if not self._same(existing,command): raise CrystalWalletConflictError("idempotency_key_payload_conflict")
                return CrystalWalletResult(existing,True)
            before=uow.wallet.get_balance(command.user_id)
            if not isinstance(before,int) or isinstance(before,bool) or before<0: raise CrystalWalletContractError("invalid_stored_balance")
            after=before+command.amount if command.direction is CrystalDirection.CREDIT else before-command.amount
            if after<0: raise CrystalWalletContractError("insufficient_crystals")
            transaction=CrystalLedgerTransaction(uow.next_transaction_id(),command.idempotency_key,command.user_id,command.direction,command.amount,before,after,command.reason_code,command.source,None,uow.now())
            uow.wallet.set_balance(command.user_id,after)
            uow.wallet.append_transaction(transaction)
            uow.commit()
            return CrystalWalletResult(transaction,False)
        except Exception:
            uow.rollback(); raise

    def compensate(self,*,original_transaction_id:str,idempotency_key:str,reason_code:str,source:str,uow:CrystalWalletUnitOfWorkPort)->CrystalWalletResult:
        if not original_transaction_id.strip(): raise CrystalWalletContractError("original_transaction_id_required")
        if not idempotency_key.strip(): raise CrystalWalletContractError("idempotency_key_required")
        try:
            existing=uow.wallet.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                if existing.original_transaction_id!=original_transaction_id or existing.reason_code!=reason_code or existing.source!=source: raise CrystalWalletConflictError("idempotency_key_payload_conflict")
                return CrystalWalletResult(existing,True)
            original=uow.wallet.get_transaction(original_transaction_id)
            if original is None: raise CrystalWalletContractError("original_transaction_not_found")
            if original.original_transaction_id is not None: raise CrystalWalletContractError("compensation_of_compensation_forbidden")
            if uow.wallet.get_compensation(original_transaction_id) is not None: raise CrystalWalletConflictError("original_already_compensated")
            direction=CrystalDirection.DEBIT if original.direction is CrystalDirection.CREDIT else CrystalDirection.CREDIT
            command=CrystalWalletCommand(idempotency_key,original.user_id,direction,original.amount,reason_code,source)
            self._validate(command)
            before=uow.wallet.get_balance(original.user_id)
            after=before+original.amount if direction is CrystalDirection.CREDIT else before-original.amount
            if after<0: raise CrystalWalletContractError("insufficient_crystals")
            transaction=CrystalLedgerTransaction(uow.next_transaction_id(),idempotency_key,original.user_id,direction,original.amount,before,after,reason_code,source,original_transaction_id,uow.now())
            uow.wallet.set_balance(original.user_id,after); uow.wallet.append_transaction(transaction); uow.commit()
            return CrystalWalletResult(transaction,False)
        except Exception:
            uow.rollback(); raise

    @staticmethod
    def _validate(command:CrystalWalletCommand)->None:
        if not command.idempotency_key.strip(): raise CrystalWalletContractError("idempotency_key_required")
        if command.user_id<=0: raise CrystalWalletContractError("user_id_must_be_positive")
        if not isinstance(command.amount,int) or isinstance(command.amount,bool): raise CrystalWalletContractError("amount_must_be_int")
        if command.amount<=0: raise CrystalWalletContractError("amount_must_be_positive")
        if not isinstance(command.direction,CrystalDirection): raise CrystalWalletContractError("invalid_direction")
        if not command.reason_code.strip(): raise CrystalWalletContractError("reason_code_required")
        if not command.source.strip(): raise CrystalWalletContractError("source_required")
    @staticmethod
    def _same(transaction,command):
        return transaction.user_id==command.user_id and transaction.direction is command.direction and transaction.amount==command.amount and transaction.reason_code==command.reason_code and transaction.source==command.source and transaction.original_transaction_id is None
