#!/usr/bin/env python3
import importlib
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# Direct execution from tools/ puts tools/, not the repository root, on sys.path.
# Insert the ROM root explicitly before importing rom_v2 flat-domain modules.
root_text = str(ROOT)
if root_text not in sys.path:
    sys.path.insert(0, root_text)
OLD = ('rom_v2/domain/events', 'tests/unit/events', 'rom_v2/domain/inactivity_reminders', 'tests/unit/inactivity_reminders', 'rom_v2/domain/ratings_history_chronicles', 'tests/unit/ratings_history_chronicles', 'rom_v2/domain/about_links_support', 'tests/unit/about_links_support', 'rom_v2/domain/dev_authorization', 'tests/unit/dev_authorization')
MODULES = ('rom_v2.domain.events', 'rom_v2.domain.inactivity_reminders', 'rom_v2.domain.ratings_history_chronicles', 'rom_v2.domain.about_links_support', 'rom_v2.domain.dev_authorization')
TESTS = ('tests_v2.test_event_schedules_rewards', 'tests_v2.test_inactivity_reminders', 'tests_v2.test_ratings_history_chronicles', 'tests_v2.test_about_links_support', 'tests_v2.test_dev_authorization')
for relative in OLD:
    assert not (ROOT / relative).exists(), f"nested path remains: {relative}"
for module in MODULES:
    importlib.import_module(module)
result = subprocess.run([sys.executable, "-m", "unittest", *TESTS, "-v"], cwd=ROOT)
if result.returncode:
    raise SystemExit(result.returncode)
print("PASS: Stage 21.15.1d flat domain remediation")
