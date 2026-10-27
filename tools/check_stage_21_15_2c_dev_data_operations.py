#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for rel in ("rom_v2/domain/dev_data_operations.py","tests_v2/test_dev_data_operations.py"):
    assert (ROOT/rel).is_file(), rel
assert not (ROOT/"rom_v2/domain/dev_data_operations").exists()
cp=subprocess.run([sys.executable,"-m","unittest","tests_v2.test_dev_data_operations","-v"],cwd=ROOT)
raise SystemExit(cp.returncode)
