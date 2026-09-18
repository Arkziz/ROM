# -*- coding: utf-8 -*-
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG_PATH = ROOT / "events" / "test_event_2026" / "config.py"
spec = importlib.util.spec_from_file_location("test_event_schedule_smoke", CONFIG_PATH)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

assert config.ENABLED is True
assert config.TIMEZONE_NAME == "Europe/Kyiv"
assert config.DATE_POLICY == "EUROPE_KYIV_LOCAL_CANONICAL"
assert config.START_LOCAL == "20.09.2026 00:17"
assert config.END_LOCAL == "20.09.2026 00:32"
assert config.START_LOCAL_TEXT == config.START_LOCAL
assert config.END_LOCAL_TEXT == config.END_LOCAL
assert config.START_AT == datetime(2026, 9, 19, 21, 17, tzinfo=timezone.utc)
assert config.END_AT == datetime(2026, 9, 19, 21, 32, tzinfo=timezone.utc)
assert not config.is_active(datetime(2026, 9, 19, 21, 16, 59, tzinfo=timezone.utc))
assert config.is_active(datetime(2026, 9, 19, 21, 17, 0, tzinfo=timezone.utc))
assert config.is_active(datetime(2026, 9, 19, 21, 31, 59, tzinfo=timezone.utc))
assert not config.is_active(datetime(2026, 9, 19, 21, 32, 0, tzinfo=timezone.utc))

# Validate winter conversion too without changing production constants.
winter = config._parse_kyiv_local("15.01.2027 12:00", "WINTER")
assert winter.astimezone(timezone.utc) == datetime(2027, 1, 15, 10, 0, tzinfo=timezone.utc)

try:
    config._parse_kyiv_local("2027-01-15 12:00", "BAD")
except ValueError as exc:
    assert "DD.MM.YYYY HH:MM" in str(exc)
else:
    raise AssertionError("invalid local format was accepted")

source = CONFIG_PATH.read_text(encoding="utf-8")
invalid = source.replace(
    'END_LOCAL = "20.09.2026 00:32"',
    'END_LOCAL = "19.09.2026 00:30"',
)
spec_bad = importlib.util.spec_from_loader("invalid_schedule_smoke", loader=None)
module_bad = importlib.util.module_from_spec(spec_bad)
try:
    exec(compile(invalid, str(CONFIG_PATH), "exec"), module_bad.__dict__)
except ValueError as exc:
    assert "END_LOCAL must be later than START_LOCAL" in str(exc)
else:
    raise AssertionError("reversed schedule was accepted")

print("TEST_EVENT_LOCAL_SCHEDULE_18_29_4I_OK")
