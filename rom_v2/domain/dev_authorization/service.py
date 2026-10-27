"""Single fail-closed authorization decision before any DEV side effect."""
from __future__ import annotations

from .model import AuthorizationDecision, AuthorizationPolicy, AuthorizationReason, AuthorizationRequest


class DevAuthorizationService:
    """Pure domain guard; it performs no database, Telegram or runtime action."""

    def __init__(self, policy: AuthorizationPolicy) -> None:
        self._policy = policy

    def authorize(self, request: AuthorizationRequest) -> AuthorizationDecision:
        """Evaluate capability, identity and operation allowlist in fail-closed order."""
        if not self._policy.dev_mode_enabled:
            return self._deny(request, AuthorizationReason.DEV_MODE_DISABLED)
        if request.caller_id not in self._policy.authorized_caller_ids:
            return self._deny(request, AuthorizationReason.CALLER_NOT_AUTHORIZED)
        if request.operation_key not in self._policy.allowed_operation_keys:
            return self._deny(request, AuthorizationReason.OPERATION_NOT_ALLOWED)
        return AuthorizationDecision(True, AuthorizationReason.ALLOWED, request.caller_id, request.operation_key, request.operation_class)

    @staticmethod
    def require_allowed(decision: AuthorizationDecision) -> None:
        """Provide a mandatory pre-side-effect assertion for application adapters."""
        if not decision.allowed:
            raise PermissionError(f"dev_authorization_denied::{decision.reason.value}")

    @staticmethod
    def _deny(request: AuthorizationRequest, reason: AuthorizationReason) -> AuthorizationDecision:
        return AuthorizationDecision(False, reason, request.caller_id, request.operation_key, request.operation_class)
