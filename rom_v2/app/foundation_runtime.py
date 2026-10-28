from __future__ import annotations

"""Framework-neutral validation for the first independently wired V2 runtime."""

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

FORBIDDEN_RUNTIME_IMPORT_ROOTS = frozenset({"handlers", "systems", "db_modules", "legacy"})
REQUIRED_FOUNDATION_PORTS = frozenset(
    {"account_uow_factory", "character_uow_factory", "clock", "random_source"}
)


@runtime_checkable
class FoundationRuntimePort(Protocol):
    """Marker protocol for dependencies supplied by the V2 composition root."""


@dataclass(frozen=True, slots=True)
class FoundationRuntimeResult:
    """Machine-readable validation result without Telegram presentation concerns."""

    ready: bool
    reason: str
    missing_ports: tuple[str, ...] = ()


def validate_foundation_runtime_ports(ports: Mapping[str, object]) -> FoundationRuntimeResult:
    """Fail closed until every required foundation dependency is provided."""
    missing = tuple(sorted(REQUIRED_FOUNDATION_PORTS.difference(ports)))
    if missing:
        return FoundationRuntimeResult(False, "missing_required_ports", missing)
    if any(ports[name] is None for name in REQUIRED_FOUNDATION_PORTS):
        empty = tuple(sorted(name for name in REQUIRED_FOUNDATION_PORTS if ports[name] is None))
        return FoundationRuntimeResult(False, "null_required_ports", empty)
    return FoundationRuntimeResult(True, "ready")


def reject_forbidden_runtime_import(module_name: str) -> None:
    """Reject V1 and legacy import roots at the V2 composition boundary."""
    root = module_name.strip().split(".", 1)[0]
    if root in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
        raise ValueError(f"forbidden_runtime_import::{root}")
