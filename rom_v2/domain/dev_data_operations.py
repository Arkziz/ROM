"""Flat API-ready DEV Give/Reset/Set application boundary.

The module is transport-agnostic and persistence-agnostic.
Authorization is passed in as an immutable decision and every mutation is delegated
through application ports inside an explicit Unit of Work.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

class DevOperationKind(str, Enum):
    GIVE = "give"
    RESET = "reset"
    SET = "set"

@dataclass(frozen=True, slots=True)
class DevAuthorization:
    allowed: bool
    actor_id: int
    reason: str
    def __post_init__(self):
        if isinstance(self.actor_id,bool) or self.actor_id<=0: raise ValueError("actor_id_must_be_positive")
        if not self.reason.strip(): raise ValueError("authorization_reason_required")

@dataclass(frozen=True, slots=True)
class DevDataCommand:
    operation_id: str
    kind: DevOperationKind
    target_id: int
    operation_key: str
    value: int | None = None
    def __post_init__(self):
        if not self.operation_id.strip(): raise ValueError("operation_id_required")
        if isinstance(self.target_id,bool) or self.target_id<=0: raise ValueError("target_id_must_be_positive")
        if not self.operation_key.strip(): raise ValueError("operation_key_required")
        if self.kind in (DevOperationKind.GIVE,DevOperationKind.SET) and (self.value is None or isinstance(self.value,bool)):
            raise ValueError("give_and_set_require_integer_value")
        if self.kind is DevOperationKind.RESET and self.value is not None: raise ValueError("reset_must_not_have_value")

@dataclass(frozen=True, slots=True)
class DevDataResult:
    operation_id: str
    kind: DevOperationKind
    target_id: int
    replayed: bool

@runtime_checkable
class DevDataOperationsPort(Protocol):
    """Application service/repository facade; implementations enforce domain invariants."""
    def give(self, command: DevDataCommand) -> None: ...
    def reset(self, command: DevDataCommand) -> None: ...
    def set_value(self, command: DevDataCommand) -> None: ...

@runtime_checkable
class DevOperationReceiptPort(Protocol):
    def exists(self, operation_id: str) -> bool: ...
    def record(self, command: DevDataCommand, actor_id: int) -> None: ...

@runtime_checkable
class UnitOfWorkPort(Protocol):
    def __enter__(self) -> "UnitOfWorkPort": ...
    def __exit__(self, exc_type, exc, tb) -> bool | None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class DevDataOperationsService:
    """Authorize first, then run exactly one invariant-preserving operation atomically."""
    def __init__(self, operations: DevDataOperationsPort, receipts: DevOperationReceiptPort, uow: UnitOfWorkPort):
        self._operations=operations; self._receipts=receipts; self._uow=uow

    def execute(self, authorization: DevAuthorization, command: DevDataCommand) -> DevDataResult:
        if not authorization.allowed: raise PermissionError(f"dev_operation_denied::{authorization.reason}")
        with self._uow:
            if self._receipts.exists(command.operation_id):
                return DevDataResult(command.operation_id,command.kind,command.target_id,True)
            try:
                if command.kind is DevOperationKind.GIVE: self._operations.give(command)
                elif command.kind is DevOperationKind.RESET: self._operations.reset(command)
                elif command.kind is DevOperationKind.SET: self._operations.set_value(command)
                else: raise ValueError(f"unsupported_dev_operation::{command.kind}")
                self._receipts.record(command,authorization.actor_id)
                self._uow.commit()
            except Exception:
                self._uow.rollback()
                raise
        return DevDataResult(command.operation_id,command.kind,command.target_id,False)
