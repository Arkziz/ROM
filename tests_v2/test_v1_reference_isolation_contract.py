from __future__ import annotations

import unittest
from pathlib import Path

from rom_v2.app.v1_reference_isolation import (
    IsolationDecision,
    ReferenceAccess,
    authorize_reference_path,
    classify_module_import,
)
from tools.check_v2_v1_reference_isolation import scan


class V1ReferenceIsolationContractTests(unittest.TestCase):
    def test_production_imports_of_v1_and_legacy_fail_closed(self) -> None:
        for module in ("handlers.start", "systems.combat", "legacy.v1.handlers.start"):
            with self.subTest(module=module):
                self.assertIs(classify_module_import(module).decision, IsolationDecision.DENY)

    def test_rom_v2_and_external_imports_remain_allowed(self) -> None:
        for module in ("rom_v2.domain.character", "datetime", "aiogram"):
            with self.subTest(module=module):
                self.assertIs(classify_module_import(module).decision, IsolationDecision.ALLOW)

    def test_audit_can_read_but_never_mutate_v1_reference(self) -> None:
        allowed = authorize_reference_path(
            "legacy/v1/handlers/start.py", ReferenceAccess.READ_ONLY_AUDIT
        )
        denied = authorize_reference_path(
            "legacy/v1/handlers/start.py", ReferenceAccess.READ_ONLY_AUDIT, mutating=True
        )
        self.assertIs(allowed.decision, IsolationDecision.ALLOW)
        self.assertIs(denied.decision, IsolationDecision.DENY)

    def test_production_filesystem_fallback_is_forbidden(self) -> None:
        result = authorize_reference_path(
            "handlers/start.py", ReferenceAccess.PRODUCTION_RUNTIME
        )
        self.assertIs(result.decision, IsolationDecision.DENY)

    def test_repository_v2_tree_has_no_v1_runtime_imports(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(scan(root)["status"], "PASS")
