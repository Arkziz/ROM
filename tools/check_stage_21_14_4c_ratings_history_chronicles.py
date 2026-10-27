#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
required = (
 "rom_v2/domain/ratings_history_chronicles/models.py",
 "rom_v2/domain/ratings_history_chronicles/ratings.py",
 "rom_v2/domain/ratings_history_chronicles/history.py",
 "rom_v2/domain/ratings_history_chronicles/chronicles.py",
 "tests/unit/ratings_history_chronicles/test_ratings_history_chronicles.py",
)
for relative in required:
    if not (ROOT / relative).is_file(): raise SystemExit(f"FAIL: missing {relative}")
result = subprocess.run([sys.executable, "-m", "unittest", "tests.unit.ratings_history_chronicles.test_ratings_history_chronicles", "-v"], cwd=ROOT)
if result.returncode: raise SystemExit(result.returncode)
print("PASS: Stage 21.14.4c ratings/history/chronicles API-ready contract")
