from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class DirectCodeOwnershipTest(unittest.TestCase):
    """Verify anti-overlay ownership without requiring external pytest."""

    def test_direct_code_ownership_verifier_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        report = root / "reports" / "stage_21_16_2_direct_code_migration_anti_overlay.json"
        cp = subprocess.run([sys.executable, "-m", "tools.verify_v2_direct_code_ownership", "--project-root", str(root), "--baseline", str(root / "reports" / "stage_21_16_2_direct_code_ownership_baseline.json"), "--json", str(report)], cwd=root, text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
