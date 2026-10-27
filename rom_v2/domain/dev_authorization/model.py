"""Fail-closed API-ready DEV authorization models."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationClass(str, Enum):
    """Resolved DEV/admin operation classes without command-name invention."""

    READ_ONLY = "read_only"
    CONTROLLED_MUTATION = "controlled_mutation"
    DESTRUCTIVE_RESET = "destructive_reset"
    ADMINISTRATIVE = "administrative"


class AuthorizationReason(str, Enum):
    ALLOWED = "allowed"
    DEV_MODE_DISABLED = "dev_mode_disabled"
    CALLER_NOT_AUTHORIZED = "caller_not_authorized"
    OPERATION_NOT_ALLOWED = "operation_not_allowed"


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    caller_id: int
    operation_key: str
    operation_class: OperationClass

    def __post_init__(self) -> None:
        if isinstance(self.caller_id, bool) or self.caller_id <= 0:
            raise ValueError("caller_id_must_be_positive")
        key = self.operation_key.strip()
        if not key:
            raise ValueError("operation_key_must_not_be_empty")
        object.__setattr__(self, "operation_key", key)


@dataclass(frozen=True, slots=True)
class AuthorizationPolicy:
    dev_mode_enabled: bool
    authorized_caller_ids: frozenset[int]
    allowed_operation_keys: frozenset[str]

    def __post_init__(self) -> None:
        if any(isinstance(value, bool) or value <= 0 for value in self.authorized_caller_ids):
            raise ValueError("authorized_caller_ids_must_be_positive")
        normalized = frozenset(key.strip() for key in self.allowed_operation_keys)
        if "" in normalized:
            raise ValueError("allowed_operation_key_must_not_be_empty")
        object.__setattr__(self, "allowed_operation_keys", normalized)


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reason: AuthorizationReason
    caller_id: int
    operation_key: str
    operation_class: OperationClass
