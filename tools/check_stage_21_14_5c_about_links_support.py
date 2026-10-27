#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
required = (
    "rom_v2/domain/about_links_support/__init__.py",
    "rom_v2/domain/about_links_support/models.py",
    "rom_v2/domain/about_links_support/service.py",
    "tests_v2/test_about_links_support.py",
)
for relative in required:
    if not (ROOT / relative).is_file():
        raise SystemExit(f"FAIL: missing {relative}")
result = subprocess.run(
    [sys.executable, "-m", "unittest", "tests_v2.test_about_links_support", "-v"],
    cwd=ROOT,
)
if result.returncode:
    raise SystemExit(result.returncode)
print("PASS: Stage 21.14.5c About/links/support API-ready contract")
