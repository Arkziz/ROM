#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
required = (
 "rom_v2/domain/dev_authorization/model.py",
 "rom_v2/domain/dev_authorization/service.py",
 "tests_v2/test_dev_authorization.py",
)
for relative in required:
    if not (ROOT / relative).is_file(): raise SystemExit(f"FAIL: missing {relative}")
result = subprocess.run([sys.executable, "-m", "unittest", "tests_v2.test_dev_authorization", "-v"], cwd=ROOT)
if result.returncode: raise SystemExit(result.returncode)
print("PASS: Stage 21.15.1c DEV authorization API-ready contract")
