"""Tests for the canonical ROM V2 CI baseline runner."""
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from tools.run_v2_ci import _compile, _content, _duplicates, _imports


class V2CiBaselineTest(unittest.TestCase):
    """Verify the current baseline and representative rejection paths."""

    def test_non_recursive_static_gates_pass(self) -> None:
        """Require static CI gates to pass without recursively invoking unit discovery."""
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(_compile(root)["status"],"PASS")
        self.assertEqual(_imports(root)["status"],"PASS")
        self.assertEqual(_duplicates(root)["status"],"PASS")
        self.assertEqual(_content(root)["status"],"PASS")

    def test_duplicate_public_symbol_is_rejected(self) -> None:
        """Reject duplicate top-level production owners."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); package=root/"rom_v2"; package.mkdir()
            (package/"one.py").write_text("def duplicate() -> None:\n    pass\n",encoding="utf-8")
            (package/"two.py").write_text("def duplicate() -> None:\n    pass\n",encoding="utf-8")
            self.assertEqual(_duplicates(root)["status"],"FAIL")

    def test_invalid_json_content_is_rejected(self) -> None:
        """Reject malformed declarative JSON content."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); content=root/"rom_v2"/"content"; content.mkdir(parents=True)
            (content/"invalid.json").write_text("{",encoding="utf-8")
            self.assertEqual(_content(root)["status"],"FAIL")


if __name__=="__main__": unittest.main()
