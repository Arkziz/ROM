"""Authoritative policy for isolating ROM V2 from V1 runtime code.

V1 is evidence, not a dependency. Audit tooling may read V1 files explicitly,
but production V2 must remain functional when V1 and ``legacy/v1`` are absent
from ``sys.path`` and from the filesystem.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Final


class ReferenceAccess(str, Enum):
    """Allowed ways in which a caller may interact with V1 material."""

    PRODUCTION_RUNTIME = "PRODUCTION_RUNTIME"
    READ_ONLY_AUDIT = "READ_ONLY_AUDIT"
    PARITY_FIXTURE_BUILD = "PARITY_FIXTURE_BUILD"


class IsolationDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


@dataclass(frozen=True, slots=True)
class IsolationResult:
    decision: IsolationDecision
    reason: str


# These are repository-root V1 namespaces. Imports under ``rom_v2`` are never
# matched merely because an internal module has a similar final component.
V1_RUNTIME_ROOTS: Final[frozenset[str]] = frozenset({
    "data", "database", "db_modules", "handlers", "keyboards", "services",
    "systems", "utils",
})
LEGACY_ROOT: Final[str] = "legacy"


def classify_module_import(module_name: str) -> IsolationResult:
    """Fail closed for any production import targeting V1 or archived V1."""
    normalized = module_name.strip().lstrip(".")
    root = normalized.split(".", 1)[0] if normalized else ""
    if root == LEGACY_ROOT:
        return IsolationResult(IsolationDecision.DENY, "legacy_runtime_import_forbidden")
    if root in V1_RUNTIME_ROOTS:
        return IsolationResult(IsolationDecision.DENY, "v1_runtime_import_forbidden")
    return IsolationResult(IsolationDecision.ALLOW, "v2_or_external_dependency")


def authorize_reference_path(
    path: str,
    access: ReferenceAccess,
    *,
    mutating: bool = False,
) -> IsolationResult:
    """Authorize explicit filesystem access to V1 evidence.

    Read-only audit and fixture construction may inspect repository files. They
    may not mutate V1, import it as runtime code, register handlers, call its
    repositories, or use it as fallback behavior.
    """
    normalized = PurePosixPath(path.replace("\\", "/"))
    parts = normalized.parts
    is_legacy = len(parts) >= 2 and parts[0] == "legacy" and parts[1] == "v1"
    is_current_v1 = bool(parts) and parts[0] in V1_RUNTIME_ROOTS
    if not (is_legacy or is_current_v1):
        return IsolationResult(IsolationDecision.ALLOW, "not_v1_reference_material")
    if mutating:
        return IsolationResult(IsolationDecision.DENY, "v1_reference_is_read_only")
    if access in {ReferenceAccess.READ_ONLY_AUDIT, ReferenceAccess.PARITY_FIXTURE_BUILD}:
        return IsolationResult(IsolationDecision.ALLOW, "explicit_read_only_reference_access")
    return IsolationResult(IsolationDecision.DENY, "production_v1_reference_access_forbidden")
