"""Tests for canonical ignored ROM V2 runtime paths."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rom_v2.runtime_paths import RuntimePaths


class RuntimePathsTest(unittest.TestCase):
    """Verify isolated and idempotent runtime directory creation."""

    def test_create_is_idempotent_and_isolated(self) -> None:
        """Create the complete tree twice without escaping the runtime root."""
        with tempfile.TemporaryDirectory() as temporary:
            paths = RuntimePaths.from_project_root(Path(temporary))
            paths.validate()
            paths.create()
            paths.create()
            self.assertEqual(
                [path.name for path in paths.directories()],
                ["db", "logs", "export", "temporary"],
            )
            self.assertTrue(all(path.is_dir() for path in paths.directories()))
            self.assertTrue(all(paths.root in path.parents for path in paths.directories()))


if __name__ == "__main__":
    unittest.main()
