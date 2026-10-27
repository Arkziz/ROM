#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(0, root_text)

DOMAIN = ROOT / "rom_v2/domain/simulator_adapters.py"
TEST = ROOT / "tests_v2/test_simulator_adapters.py"
assert DOMAIN.is_file(), "missing flat simulator adapter module"
assert TEST.is_file(), "missing flat simulator adapter tests"
assert not (ROOT / "rom_v2/domain/simulator_adapters").exists(), "nested simulator package is forbidden"
source = DOMAIN.read_text(encoding="utf-8")
ast.parse(source)
assert "sqlite3" not in source
assert "game.db" not in source
assert "systems.simulation" not in source
importlib.import_module("rom_v2.domain.simulator_adapters")
result = subprocess.run(
    [sys.executable, "-m", "unittest", "tests_v2.test_simulator_adapters", "-v"],
    cwd=ROOT,
    check=False,
)
if result.returncode:
    raise SystemExit(result.returncode)
print("PASS: Stage 21.15.3c flat simulator adapters")
