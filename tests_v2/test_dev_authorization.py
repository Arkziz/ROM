from __future__ import annotations
import unittest
from rom_v2.domain.dev_authorization import (
    AuthorizationPolicy, AuthorizationReason, AuthorizationRequest,
    DevAuthorizationService, OperationClass,
)

class DevAuthorizationTests(unittest.TestCase):
    def request(self, caller=10, key="diagnostic"):
        return AuthorizationRequest(caller, key, OperationClass.READ_ONLY)

    def test_disabled_dev_mode_denies_before_identity(self):
        service = DevAuthorizationService(AuthorizationPolicy(False, frozenset({10}), frozenset({"diagnostic"})))
        decision = service.authorize(self.request())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AuthorizationReason.DEV_MODE_DISABLED)

    def test_unauthorized_caller_is_blocked(self):
        service = DevAuthorizationService(AuthorizationPolicy(True, frozenset({10}), frozenset({"diagnostic"})))
        decision = service.authorize(self.request(caller=11))
        self.assertEqual(decision.reason, AuthorizationReason.CALLER_NOT_AUTHORIZED)

    def test_unlisted_operation_is_blocked(self):
        service = DevAuthorizationService(AuthorizationPolicy(True, frozenset({10}), frozenset({"diagnostic"})))
        decision = service.authorize(self.request(key="unknown"))
        self.assertEqual(decision.reason, AuthorizationReason.OPERATION_NOT_ALLOWED)

    def test_authorized_operation_is_allowed(self):
        service = DevAuthorizationService(AuthorizationPolicy(True, frozenset({10}), frozenset({"diagnostic"})))
        decision = service.authorize(self.request())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, AuthorizationReason.ALLOWED)

    def test_require_allowed_fails_before_adapter_side_effect(self):
        service = DevAuthorizationService(AuthorizationPolicy(True, frozenset({10}), frozenset()))
        with self.assertRaisesRegex(PermissionError, "operation_not_allowed"):
            service.require_allowed(service.authorize(self.request()))

    def test_all_operation_classes_are_explicit(self):
        self.assertEqual({item.value for item in OperationClass}, {
            "read_only", "controlled_mutation", "destructive_reset", "administrative"
        })

    def test_invalid_identity_and_empty_keys_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "caller_id"):
            AuthorizationRequest(0, "x", OperationClass.READ_ONLY)
        with self.assertRaisesRegex(ValueError, "operation_key"):
            AuthorizationRequest(1, " ", OperationClass.READ_ONLY)
        with self.assertRaisesRegex(ValueError, "authorized_caller_ids"):
            AuthorizationPolicy(True, frozenset({0}), frozenset())

    def test_domain_has_no_transport_database_or_environment_access(self):
        import inspect
        import rom_v2.domain.dev_authorization as service
        source = inspect.getsource(service)
        for forbidden in ("sqlite3", "os.getenv", "aiogram", "telegram", "execute("):
            self.assertNotIn(forbidden, source)

if __name__ == "__main__": unittest.main()
