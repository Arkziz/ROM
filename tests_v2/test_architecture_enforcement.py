"""Tests for the ROM V2 architecture enforcement verifier."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify_v2_architecture import verify


class ArchitectureEnforcementTest(unittest.TestCase):
    """Verify happy path and representative architecture rejections."""

    def _write(self, root: Path, relative: str, text: str) -> None:
        """Write one temporary Python module for verifier testing."""
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_current_project_passes(self) -> None:
        """Require the physical project tree to satisfy the verifier."""
        project_root = Path(__file__).resolve().parents[1]
        self.assertEqual(verify(project_root)["summary"]["status"], "PASS")

    def test_v1_import_is_rejected(self) -> None:
        """Reject a direct dependency on a legacy V1 runtime root."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for required in REQUIRED_FOR_FIXTURE:
                self._write(root, required, '"""fixture"""\n')
            self._write(root, "rom_v2/domain/model.py", '"""fixture"""\nimport handlers\n')
            rules = {item["rule"] for item in verify(root)["violations"]}
            self.assertIn("V1_RUNTIME_IMPORT", rules)

    def test_outward_layer_import_is_rejected(self) -> None:
        """Reject a domain dependency on infrastructure."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for required in REQUIRED_FOR_FIXTURE:
                self._write(root, required, '"""fixture"""\n')
            self._write(root, "rom_v2/domain/model.py", '"""fixture"""\nimport rom_v2.infrastructure\n')
            rules = {item["rule"] for item in verify(root)["violations"]}
            self.assertIn("OUTWARD_LAYER_IMPORT", rules)


REQUIRED_FOR_FIXTURE = {
    "rom_v2/__init__.py", "rom_v2/main.py", "rom_v2/bootstrap.py", "rom_v2/config.py",
    "rom_v2/container.py", "rom_v2/lifecycle.py", "rom_v2/runtime_paths.py", "rom_v2/settings.py",
    "rom_v2/structured_logging.py", "rom_v2/domain/__init__.py", "rom_v2/application/__init__.py",
    "rom_v2/application/ports/repositories.py", "rom_v2/application/ports/unit_of_work.py",
    "rom_v2/application/ports/clock.py", "rom_v2/application/ports/random_source.py",
    "rom_v2/infrastructure/__init__.py", "rom_v2/app/__init__.py", "rom_v2/content/__init__.py",
}


if __name__ == "__main__":
    unittest.main()
